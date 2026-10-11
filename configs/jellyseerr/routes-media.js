"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const radarr_1 = __importDefault(require("../api/servarr/radarr"));
const sonarr_1 = __importDefault(require("../api/servarr/sonarr"));
const tautulli_1 = __importDefault(require("../api/tautulli"));
const themoviedb_1 = __importDefault(require("../api/themoviedb"));
const media_1 = require("../constants/media");
const datasource_1 = require("../datasource");
const Media_1 = __importDefault(require("../entity/Media"));
const Season_1 = __importDefault(require("../entity/Season"));
const User_1 = require("../entity/User");
const permissions_1 = require("../lib/permissions");
const settings_1 = require("../lib/settings");
const logger_1 = __importDefault(require("../logger"));
const auth_1 = require("../middleware/auth");
const express_1 = require("express");
const typeorm_1 = require("typeorm");
const mediaRoutes = (0, express_1.Router)();
mediaRoutes.get('/', async (req, res, next) => {
    const mediaRepository = (0, datasource_1.getRepository)(Media_1.default);
    const pageSize = req.query.take ? Number(req.query.take) : 20;
    const skip = req.query.skip ? Number(req.query.skip) : 0;
    let statusFilter = undefined;
    switch (req.query.filter) {
        case 'available':
            statusFilter = media_1.MediaStatus.AVAILABLE;
            break;
        case 'partial':
            statusFilter = media_1.MediaStatus.PARTIALLY_AVAILABLE;
            break;
        case 'allavailable':
            statusFilter = (0, typeorm_1.In)([
                media_1.MediaStatus.AVAILABLE,
                media_1.MediaStatus.PARTIALLY_AVAILABLE,
            ]);
            break;
        case 'processing':
            statusFilter = media_1.MediaStatus.PROCESSING;
            break;
        case 'pending':
            statusFilter = media_1.MediaStatus.PENDING;
            break;
        default:
            statusFilter = undefined;
    }
    let sortFilter = {
        id: 'DESC',
    };
    switch (req.query.sort) {
        case 'modified':
            sortFilter = {
                updatedAt: 'DESC',
            };
            break;
        case 'mediaAdded':
            sortFilter = {
                mediaAddedAt: 'DESC',
            };
    }
    try {
        const [media, mediaCount] = await mediaRepository.findAndCount({
            order: sortFilter,
            where: statusFilter && {
                status: statusFilter,
            },
            take: pageSize,
            skip,
        });
        return res.status(200).json({
            pageInfo: {
                pages: Math.ceil(mediaCount / pageSize),
                pageSize,
                results: mediaCount,
                page: Math.ceil(skip / pageSize) + 1,
            },
            results: media,
        });
    }
    catch (e) {
        next({ status: 500, message: e.message });
    }
});
mediaRoutes.post('/:id/:status', (0, auth_1.isAuthenticated)(permissions_1.Permission.MANAGE_REQUESTS), async (req, res, next) => {
    const mediaRepository = (0, datasource_1.getRepository)(Media_1.default);
    const seasonRepository = (0, datasource_1.getRepository)(Season_1.default);
    const media = await mediaRepository.findOne({
        where: { id: Number(req.params.id) },
    });
    if (!media) {
        return next({ status: 404, message: 'Media does not exist.' });
    }
    const is4k = Boolean(req.body.is4k);
    switch (req.params.status) {
        case 'available':
            media[is4k ? 'status4k' : 'status'] = media_1.MediaStatus.AVAILABLE;
            if (media.mediaType === media_1.MediaType.TV) {
                const expectedSeasons = req.body.seasons ?? [];
                for (const expectedSeason of expectedSeasons) {
                    let season = media.seasons.find((s) => s.seasonNumber === expectedSeason?.seasonNumber);
                    if (!season) {
                        // Create the season if it doesn't exist
                        season = seasonRepository.create({
                            seasonNumber: expectedSeason?.seasonNumber,
                        });
                        media.seasons.push(season);
                    }
                    season[is4k ? 'status4k' : 'status'] = media_1.MediaStatus.AVAILABLE;
                }
            }
            break;
        case 'partial':
            if (media.mediaType === media_1.MediaType.MOVIE) {
                return next({
                    status: 400,
                    message: 'Only series can be set to be partially available',
                });
            }
            media.status = media_1.MediaStatus.PARTIALLY_AVAILABLE;
            break;
        case 'processing':
            media.status = media_1.MediaStatus.PROCESSING;
            break;
        case 'pending':
            media.status = media_1.MediaStatus.PENDING;
            break;
        case 'unknown':
            media.status = media_1.MediaStatus.UNKNOWN;
    }
    await mediaRepository.save(media);
    return res.status(200).json(media);
});
mediaRoutes.post('/:id/delete-requested', (0, auth_1.isAuthenticated)(permissions_1.Permission.MANAGE_REQUESTS), async (req, res, next) => {
    try {
        const { deleteRequestedMedia } = require("/app/config/custom-delete-requested.js");
        const summary = await deleteRequestedMedia({
            mediaId: req.params.id,
            pauseDownload: req.body?.pauseDownload !== false,
            deleteFiles: req.body?.deleteFiles !== false,
            deleteMedia: req.body?.deleteMedia !== false,
        });
        return res.status(200).json(summary);
    } catch (e) {
        next({ status: 500, message: e.message });
    }
});
mediaRoutes.delete('/:id', (0, auth_1.isAuthenticated)(permissions_1.Permission.MANAGE_REQUESTS), async (req, res, next) => {
    try {
        const mediaRepository = (0, datasource_1.getRepository)(Media_1.default);
        const media = await mediaRepository.findOneOrFail({
            where: { id: Number(req.params.id) },
        });
        await mediaRepository.remove(media);
        return res.status(204).send();
    }
    catch (e) {
        logger_1.default.error('Something went wrong fetching media in delete request', {
            label: 'Media',
            message: e.message,
        });
        next({ status: 404, message: 'Media not found' });
    }
});
mediaRoutes.delete('/:id/file', (0, auth_1.isAuthenticated)(permissions_1.Permission.MANAGE_REQUESTS), async (req, res, next) => {
    try {
        const settings = (0, settings_1.getSettings)();
        const mediaRepository = (0, datasource_1.getRepository)(Media_1.default);
        const media = await mediaRepository.findOneOrFail({
            where: { id: Number(req.params.id) },
        });
        const is4k = req.query.is4k === 'true';
        const isMovie = media.mediaType === media_1.MediaType.MOVIE;
        let serviceSettings;
        if (isMovie) {
            serviceSettings = settings.radarr.find((radarr) => radarr.isDefault && radarr.is4k === is4k);
        }
        else {
            serviceSettings = settings.sonarr.find((sonarr) => sonarr.isDefault && sonarr.is4k === is4k);
        }
        if (media.serviceId &&
            media.serviceId >= 0 &&
            serviceSettings?.id !== media.serviceId) {
            if (isMovie) {
                serviceSettings = settings.radarr.find((radarr) => radarr.id === media.serviceId);
            }
            else {
                serviceSettings = settings.sonarr.find((sonarr) => sonarr.id === media.serviceId);
            }
        }
        if (!serviceSettings) {
            logger_1.default.warn(`There is no default ${is4k ? '4K ' : '' + isMovie ? 'Radarr' : 'Sonarr'}/ server configured. Did you set any of your ${is4k ? '4K ' : '' + isMovie ? 'Radarr' : 'Sonarr'} servers as default?`, {
                label: 'Media Request',
                mediaId: media.id,
            });
            return;
        }
        let service;
        if (isMovie) {
            service = new radarr_1.default({
                apiKey: serviceSettings?.apiKey,
                url: radarr_1.default.buildUrl(serviceSettings, '/api/v3'),
            });
        }
        else {
            service = new sonarr_1.default({
                apiKey: serviceSettings?.apiKey,
                url: sonarr_1.default.buildUrl(serviceSettings, '/api/v3'),
            });
        }
        if (isMovie) {
            await service.removeMovie(parseInt(is4k
                ? media.externalServiceSlug4k
                : media.externalServiceSlug));
        }
        else {
            const tmdb = new themoviedb_1.default();
            const series = await tmdb.getTvShow({ tvId: media.tmdbId });
            const tvdbId = series.external_ids.tvdb_id ?? media.tvdbId;
            if (!tvdbId) {
                throw new Error('TVDB ID not found');
            }
            await service.removeSerie(tvdbId);
        }
        return res.status(204).send();
    }
    catch (e) {
        logger_1.default.error('Something went wrong fetching media in delete request', {
            label: 'Media',
            message: e.message,
        });
        next({ status: 404, message: 'Media not found' });
    }
});
mediaRoutes.get('/:id/watch_data', (0, auth_1.isAuthenticated)(permissions_1.Permission.ADMIN), async (req, res, next) => {
    const settings = (0, settings_1.getSettings)().tautulli;
    if (!settings.hostname || !settings.port || !settings.apiKey) {
        return next({
            status: 404,
            message: 'Tautulli API not configured.',
        });
    }
    const media = await (0, datasource_1.getRepository)(Media_1.default).findOne({
        where: { id: Number(req.params.id) },
    });
    if (!media) {
        return next({ status: 404, message: 'Media does not exist.' });
    }
    try {
        const tautulli = new tautulli_1.default(settings);
        const userRepository = (0, datasource_1.getRepository)(User_1.User);
        const response = {};
        if (media.ratingKey) {
            const watchStats = await tautulli.getMediaWatchStats(media.ratingKey);
            const watchUsers = await tautulli.getMediaWatchUsers(media.ratingKey);
            const users = await userRepository
                .createQueryBuilder('user')
                .where('user.plexId IN (:...plexIds)', {
                plexIds: watchUsers.map((u) => u.user_id),
            })
                .getMany();
            const playCount = watchStats.find((i) => i.query_days == 0)?.total_plays ?? 0;
            const playCount7Days = watchStats.find((i) => i.query_days == 7)?.total_plays ?? 0;
            const playCount30Days = watchStats.find((i) => i.query_days == 30)?.total_plays ?? 0;
            response.data = {
                users: users,
                playCount,
                playCount7Days,
                playCount30Days,
            };
        }
        if (media.ratingKey4k) {
            const watchStats4k = await tautulli.getMediaWatchStats(media.ratingKey4k);
            const watchUsers4k = await tautulli.getMediaWatchUsers(media.ratingKey4k);
            const users = await userRepository
                .createQueryBuilder('user')
                .where('user.plexId IN (:...plexIds)', {
                plexIds: watchUsers4k.map((u) => u.user_id),
            })
                .getMany();
            const playCount = watchStats4k.find((i) => i.query_days == 0)?.total_plays ?? 0;
            const playCount7Days = watchStats4k.find((i) => i.query_days == 7)?.total_plays ?? 0;
            const playCount30Days = watchStats4k.find((i) => i.query_days == 30)?.total_plays ?? 0;
            response.data4k = {
                users,
                playCount,
                playCount7Days,
                playCount30Days,
            };
        }
        return res.status(200).json(response);
    }
    catch (e) {
        logger_1.default.error('Something went wrong fetching media watch data', {
            label: 'API',
            errorMessage: e.message,
            mediaId: req.params.id,
        });
        next({ status: 500, message: 'Failed to fetch watch data.' });
    }
});
exports.default = mediaRoutes;
