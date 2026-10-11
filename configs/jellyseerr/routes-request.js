"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const radarr_1 = __importDefault(require("../api/servarr/radarr"));
const sonarr_1 = __importDefault(require("../api/servarr/sonarr"));
const media_1 = require("../constants/media");
const datasource_1 = require("../datasource");
const Media_1 = __importDefault(require("../entity/Media"));
const MediaRequest_1 = require("../entity/MediaRequest");
const SeasonRequest_1 = __importDefault(require("../entity/SeasonRequest"));
const User_1 = require("../entity/User");
const permissions_1 = require("../lib/permissions");
const settings_1 = require("../lib/settings");
const logger_1 = __importDefault(require("../logger"));
const auth_1 = require("../middleware/auth");
const express_1 = require("express");
const requestRoutes = (0, express_1.Router)();
requestRoutes.get('/', async (req, res, next) => {
    try {
        const pageSize = req.query.take ? Number(req.query.take) : 10;
        const skip = req.query.skip ? Number(req.query.skip) : 0;
        const requestedBy = req.query.requestedBy
            ? Number(req.query.requestedBy)
            : null;
        const mediaType = req.query.mediaType || 'all';
        let statusFilter;
        switch (req.query.filter) {
            case 'approved':
            case 'processing':
                statusFilter = [media_1.MediaRequestStatus.APPROVED];
                break;
            case 'pending':
                statusFilter = [media_1.MediaRequestStatus.PENDING];
                break;
            case 'unavailable':
                statusFilter = [
                    media_1.MediaRequestStatus.PENDING,
                    media_1.MediaRequestStatus.APPROVED,
                ];
                break;
            case 'failed':
                statusFilter = [media_1.MediaRequestStatus.FAILED];
                break;
            case 'completed':
            case 'available':
            case 'deleted':
                statusFilter = [media_1.MediaRequestStatus.COMPLETED];
                break;
            default:
                statusFilter = [
                    media_1.MediaRequestStatus.PENDING,
                    media_1.MediaRequestStatus.APPROVED,
                    media_1.MediaRequestStatus.DECLINED,
                    media_1.MediaRequestStatus.FAILED,
                    media_1.MediaRequestStatus.COMPLETED,
                ];
        }
        let mediaStatusFilter;
        switch (req.query.filter) {
            case 'available':
                mediaStatusFilter = [media_1.MediaStatus.AVAILABLE];
                break;
            case 'processing':
            case 'unavailable':
                mediaStatusFilter = [
                    media_1.MediaStatus.UNKNOWN,
                    media_1.MediaStatus.PENDING,
                    media_1.MediaStatus.PROCESSING,
                    media_1.MediaStatus.PARTIALLY_AVAILABLE,
                ];
                break;
            case 'deleted':
                mediaStatusFilter = [media_1.MediaStatus.DELETED];
                break;
            default:
                mediaStatusFilter = [
                    media_1.MediaStatus.UNKNOWN,
                    media_1.MediaStatus.PENDING,
                    media_1.MediaStatus.PROCESSING,
                    media_1.MediaStatus.PARTIALLY_AVAILABLE,
                    media_1.MediaStatus.AVAILABLE,
                    media_1.MediaStatus.DELETED,
                ];
        }
        let sortFilter;
        let sortDirection;
        switch (req.query.sort) {
            case 'modified':
                sortFilter = 'request.updatedAt';
                break;
            default:
                sortFilter = 'request.id';
        }
        switch (req.query.sortDirection) {
            case 'asc':
                sortDirection = 'ASC';
                break;
            default:
                sortDirection = 'DESC';
        }
        let query = (0, datasource_1.getRepository)(MediaRequest_1.MediaRequest)
            .createQueryBuilder('request')
            .leftJoinAndSelect('request.media', 'media')
            .leftJoinAndSelect('request.seasons', 'seasons')
            .leftJoinAndSelect('request.modifiedBy', 'modifiedBy')
            .leftJoinAndSelect('request.requestedBy', 'requestedBy')
            .where('request.status IN (:...requestStatus)', {
            requestStatus: statusFilter,
        })
            .andWhere('((request.is4k = false AND media.status IN (:...mediaStatus)) OR (request.is4k = true AND media.status4k IN (:...mediaStatus)))', {
            mediaStatus: mediaStatusFilter,
        });
        if (!req.user?.hasPermission([permissions_1.Permission.MANAGE_REQUESTS, permissions_1.Permission.REQUEST_VIEW], { type: 'or' })) {
            if (requestedBy && requestedBy !== req.user?.id) {
                return next({
                    status: 403,
                    message: "You do not have permission to view this user's requests.",
                });
            }
            query = query.andWhere('requestedBy.id = :id', {
                id: req.user?.id,
            });
        }
        else if (requestedBy) {
            query = query.andWhere('requestedBy.id = :id', {
                id: requestedBy,
            });
        }
        switch (mediaType) {
            case 'all':
                break;
            case 'movie':
                query = query.andWhere('request.type = :type', {
                    type: media_1.MediaType.MOVIE,
                });
                break;
            case 'tv':
                query = query.andWhere('request.type = :type', {
                    type: media_1.MediaType.TV,
                });
                break;
        }
        const [requests, requestCount] = await query
            .orderBy(sortFilter, sortDirection)
            .take(pageSize)
            .skip(skip)
            .getManyAndCount();
        const settings = (0, settings_1.getSettings)();
        // get all quality profiles for every configured sonarr server
        const sonarrServers = await Promise.all(settings.sonarr.map(async (sonarrSetting) => {
            const sonarr = new sonarr_1.default({
                apiKey: sonarrSetting.apiKey,
                url: sonarr_1.default.buildUrl(sonarrSetting, '/api/v3'),
            });
            return {
                id: sonarrSetting.id,
                profiles: await sonarr.getProfiles().catch(() => undefined),
            };
        }));
        // get all quality profiles for every configured radarr server
        const radarrServers = await Promise.all(settings.radarr.map(async (radarrSetting) => {
            const radarr = new radarr_1.default({
                apiKey: radarrSetting.apiKey,
                url: radarr_1.default.buildUrl(radarrSetting, '/api/v3'),
            });
            return {
                id: radarrSetting.id,
                profiles: await radarr.getProfiles().catch(() => undefined),
            };
        }));
        // add profile names to the media requests, with undefined if not found
        let mappedRequests = requests.map((r) => {
            switch (r.type) {
                case media_1.MediaType.MOVIE: {
                    const profileName = radarrServers
                        .find((serverr) => serverr.id === r.serverId)
                        ?.profiles?.find((profile) => profile.id === r.profileId)?.name;
                    return {
                        ...r,
                        profileName,
                    };
                }
                case media_1.MediaType.TV: {
                    return {
                        ...r,
                        profileName: sonarrServers
                            .find((serverr) => serverr.id === r.serverId)
                            ?.profiles?.find((profile) => profile.id === r.profileId)?.name,
                    };
                }
            }
        });
        // add canRemove prop if user has permission
        if (req.user?.hasPermission(permissions_1.Permission.MANAGE_REQUESTS)) {
            mappedRequests = mappedRequests.map((r) => {
                switch (r.type) {
                    case media_1.MediaType.MOVIE: {
                        return {
                            ...r,
                            // check if the radarr server for this request is configured
                            canRemove: radarrServers.some((server) => server.id ===
                                (r.is4k ? r.media.serviceId4k : r.media.serviceId)),
                        };
                    }
                    case media_1.MediaType.TV: {
                        return {
                            ...r,
                            // check if the sonarr server for this request is configured
                            canRemove: sonarrServers.some((server) => server.id ===
                                (r.is4k ? r.media.serviceId4k : r.media.serviceId)),
                        };
                    }
                }
            });
        }
        return res.status(200).json({
            pageInfo: {
                pages: Math.ceil(requestCount / pageSize),
                pageSize,
                results: requestCount,
                page: Math.ceil(skip / pageSize) + 1,
            },
            results: mappedRequests,
        });
    }
    catch (e) {
        next({ status: 500, message: e.message });
    }
});
requestRoutes.post('/', async (req, res, next) => {
    try {
        if (!req.user) {
            return next({
                status: 401,
                message: 'You must be logged in to request media.',
            });
        }
        const request = await MediaRequest_1.MediaRequest.request(req.body, req.user);
        return res.status(201).json(request);
    }
    catch (error) {
        if (!(error instanceof Error)) {
            return;
        }
        switch (error.constructor) {
            case MediaRequest_1.RequestPermissionError:
            case MediaRequest_1.QuotaRestrictedError:
                return next({ status: 403, message: error.message });
            case MediaRequest_1.DuplicateMediaRequestError:
                return next({ status: 409, message: error.message });
            case MediaRequest_1.NoSeasonsAvailableError:
                return next({ status: 202, message: error.message });
            case MediaRequest_1.BlacklistedMediaError:
                return next({ status: 403, message: error.message });
            default:
                return next({ status: 500, message: error.message });
        }
    }
});
requestRoutes.get('/count', async (_req, res, next) => {
    const requestRepository = (0, datasource_1.getRepository)(MediaRequest_1.MediaRequest);
    try {
        const query = requestRepository
            .createQueryBuilder('request')
            .innerJoinAndSelect('request.media', 'media');
        const totalCount = await query.getCount();
        const movieCount = await query
            .where('request.type = :requestType', {
            requestType: media_1.MediaType.MOVIE,
        })
            .getCount();
        const tvCount = await query
            .where('request.type = :requestType', {
            requestType: media_1.MediaType.TV,
        })
            .getCount();
        const pendingCount = await query
            .where('request.status = :requestStatus', {
            requestStatus: media_1.MediaRequestStatus.PENDING,
        })
            .getCount();
        const approvedCount = await query
            .where('request.status = :requestStatus', {
            requestStatus: media_1.MediaRequestStatus.APPROVED,
        })
            .getCount();
        const declinedCount = await query
            .where('request.status = :requestStatus', {
            requestStatus: media_1.MediaRequestStatus.DECLINED,
        })
            .getCount();
        const processingCount = await query
            .where('request.status = :requestStatus', {
            requestStatus: media_1.MediaRequestStatus.APPROVED,
        })
            .andWhere('((request.is4k = false AND media.status != :availableStatus) OR (request.is4k = true AND media.status4k != :availableStatus))', {
            availableStatus: media_1.MediaStatus.AVAILABLE,
        })
            .getCount();
        const availableCount = await query
            .where('request.status = :requestStatus', {
            requestStatus: media_1.MediaRequestStatus.APPROVED,
        })
            .andWhere('((request.is4k = false AND media.status = :availableStatus) OR (request.is4k = true AND media.status4k = :availableStatus))', {
            availableStatus: media_1.MediaStatus.AVAILABLE,
        })
            .getCount();
        return res.status(200).json({
            total: totalCount,
            movie: movieCount,
            tv: tvCount,
            pending: pendingCount,
            approved: approvedCount,
            declined: declinedCount,
            processing: processingCount,
            available: availableCount,
        });
    }
    catch (e) {
        logger_1.default.error('Something went wrong retrieving request counts', {
            label: 'API',
            errorMessage: e.message,
        });
        next({ status: 500, message: 'Unable to retrieve request counts.' });
    }
});
requestRoutes.get('/:requestId', async (req, res, next) => {
    const requestRepository = (0, datasource_1.getRepository)(MediaRequest_1.MediaRequest);
    try {
        const request = await requestRepository.findOneOrFail({
            where: { id: Number(req.params.requestId) },
            relations: { requestedBy: true, modifiedBy: true },
        });
        if (request.requestedBy.id !== req.user?.id &&
            !req.user?.hasPermission([permissions_1.Permission.MANAGE_REQUESTS, permissions_1.Permission.REQUEST_VIEW], { type: 'or' })) {
            return next({
                status: 403,
                message: 'You do not have permission to view this request.',
            });
        }
        return res.status(200).json(request);
    }
    catch (e) {
        logger_1.default.debug('Failed to retrieve request.', {
            label: 'API',
            errorMessage: e.message,
        });
        next({ status: 404, message: 'Request not found.' });
    }
});
requestRoutes.put('/:requestId', async (req, res, next) => {
    const requestRepository = (0, datasource_1.getRepository)(MediaRequest_1.MediaRequest);
    const userRepository = (0, datasource_1.getRepository)(User_1.User);
    try {
        const request = await requestRepository.findOne({
            where: {
                id: Number(req.params.requestId),
            },
        });
        if (!request) {
            return next({ status: 404, message: 'Request not found.' });
        }
        if ((request.requestedBy.id !== req.user?.id ||
            (req.body.mediaType !== 'tv' &&
                !req.user?.hasPermission(permissions_1.Permission.REQUEST_ADVANCED))) &&
            !req.user?.hasPermission(permissions_1.Permission.MANAGE_REQUESTS)) {
            return next({
                status: 403,
                message: 'You do not have permission to modify this request.',
            });
        }
        let requestUser = request.requestedBy;
        if (req.body.userId &&
            req.body.userId !== request.requestedBy.id &&
            !req.user?.hasPermission([
                permissions_1.Permission.MANAGE_USERS,
                permissions_1.Permission.MANAGE_REQUESTS,
            ])) {
            return next({
                status: 403,
                message: 'You do not have permission to modify the request user.',
            });
        }
        else if (req.body.userId) {
            requestUser = await userRepository.findOneOrFail({
                where: { id: req.body.userId },
            });
        }
        if (req.body.mediaType === media_1.MediaType.MOVIE) {
            request.serverId = req.body.serverId;
            request.profileId = req.body.profileId;
            request.rootFolder = req.body.rootFolder;
            request.tags = req.body.tags;
            request.requestedBy = requestUser;
            requestRepository.save(request);
        }
        else if (req.body.mediaType === media_1.MediaType.TV) {
            const mediaRepository = (0, datasource_1.getRepository)(Media_1.default);
            request.serverId = req.body.serverId;
            request.profileId = req.body.profileId;
            request.rootFolder = req.body.rootFolder;
            request.languageProfileId = req.body.languageProfileId;
            request.tags = req.body.tags;
            request.requestedBy = requestUser;
            const requestedSeasons = req.body.seasons;
            if (!requestedSeasons || requestedSeasons.length === 0) {
                throw new Error('Missing seasons. If you want to cancel a series request, use the DELETE method.');
            }
            // Get existing media so we can work with all the requests
            const media = await mediaRepository.findOneOrFail({
                where: { tmdbId: request.media.tmdbId, mediaType: media_1.MediaType.TV },
                relations: { requests: true },
            });
            // Get all requested seasons that are not part of this request we are editing
            const existingSeasons = media.requests
                .filter((r) => r.is4k === request.is4k &&
                r.id !== request.id &&
                r.status !== media_1.MediaRequestStatus.DECLINED &&
                r.status !== media_1.MediaRequestStatus.COMPLETED)
                .reduce((seasons, r) => {
                const combinedSeasons = r.seasons.map((season) => season.seasonNumber);
                return [...seasons, ...combinedSeasons];
            }, []);
            const filteredSeasons = requestedSeasons.filter((rs) => !existingSeasons.includes(rs));
            if (filteredSeasons.length === 0) {
                return next({
                    status: 202,
                    message: 'No seasons available to request',
                });
            }
            const newSeasons = requestedSeasons.filter((sn) => !request.seasons.map((s) => s.seasonNumber).includes(sn));
            request.seasons = request.seasons.filter((rs) => filteredSeasons.includes(rs.seasonNumber));
            if (newSeasons.length > 0) {
                logger_1.default.debug('Adding new seasons to request', {
                    label: 'Media Request',
                    newSeasons,
                });
                request.seasons.push(...newSeasons.map((ns) => new SeasonRequest_1.default({
                    seasonNumber: ns,
                    status: media_1.MediaRequestStatus.PENDING,
                })));
            }
            await requestRepository.save(request);
        }
        return res.status(200).json(request);
    }
    catch (e) {
        next({ status: 500, message: e.message });
    }
});
requestRoutes.post('/:requestId/delete-requested', async (req, res, next) => {
    try {
        const { deleteRequestedMedia } = require("/app/config/custom-delete-requested.js");
        const summary = await deleteRequestedMedia({
            requestId: req.params.requestId,
            pauseDownload: req.body?.pauseDownload !== false,
            deleteFiles: req.body?.deleteFiles !== false,
            deleteMedia: req.body?.deleteMedia !== false,
        });
        return res.status(200).json(summary);
    } catch (e) {
        next({ status: 500, message: e.message });
    }
});
requestRoutes.delete('/:requestId', async (req, res, next) => {
    const requestRepository = (0, datasource_1.getRepository)(MediaRequest_1.MediaRequest);
    try {
        const request = await requestRepository.findOneOrFail({
            where: { id: Number(req.params.requestId) },
            relations: { requestedBy: true, modifiedBy: true, media: true },
        });
        if (!req.user?.hasPermission(permissions_1.Permission.MANAGE_REQUESTS) &&
            request.requestedBy.id !== req.user?.id &&
            request.status !== 1) {
            return next({
                status: 401,
                message: "You do not have permission to delete this request.",
            });
        }
        const pauseDownload = req.query.pauseDownload !== "false";
        const deleteFiles = req.query.deleteFiles !== "false";
        const deleteMedia = req.query.deleteMedia !== "false";
        try {
            const { deleteRequestedMedia } = require("/app/config/custom-delete-requested.js");
            const summary = await deleteRequestedMedia({
                requestId: request.id,
                pauseDownload,
                deleteFiles,
                deleteMedia,
            });
            logger_1.default.info("[DeleteRequested] Completed delete-requested via DELETE /api/v1/request/" + request.id, summary);
            return res.status(204).send();
        } catch (err) {
            logger_1.default.warn("[DeleteRequested] Fallback to standard request removal: " + err.message);
            await requestRepository.remove(request);
            return res.status(204).send();
        }
    }
    catch (e) {
        logger_1.default.error("Something went wrong deleting a request.", {
            label: "API",
            errorMessage: e.message,
        });
        next({ status: 404, message: "Request not found." });
    }
});
requestRoutes.post('/:requestId/retry', (0, auth_1.isAuthenticated)(permissions_1.Permission.MANAGE_REQUESTS), async (req, res, next) => {
    const requestRepository = (0, datasource_1.getRepository)(MediaRequest_1.MediaRequest);
    try {
        const request = await requestRepository.findOneOrFail({
            where: { id: Number(req.params.requestId) },
            relations: { requestedBy: true, modifiedBy: true },
        });
        // this also triggers updating the parent media's status & sending to *arr
        request.status = media_1.MediaRequestStatus.APPROVED;
        await requestRepository.save(request);
        return res.status(200).json(request);
    }
    catch (e) {
        logger_1.default.error('Error processing request retry', {
            label: 'Media Request',
            message: e.message,
        });
        next({ status: 404, message: 'Request not found.' });
    }
});
requestRoutes.post('/:requestId/:status', (0, auth_1.isAuthenticated)(permissions_1.Permission.MANAGE_REQUESTS), async (req, res, next) => {
    const requestRepository = (0, datasource_1.getRepository)(MediaRequest_1.MediaRequest);
    try {
        const request = await requestRepository.findOneOrFail({
            where: { id: Number(req.params.requestId) },
            relations: { requestedBy: true, modifiedBy: true },
        });
        let newStatus;
        switch (req.params.status) {
            case 'pending':
                newStatus = media_1.MediaRequestStatus.PENDING;
                break;
            case 'approve':
                newStatus = media_1.MediaRequestStatus.APPROVED;
                break;
            case 'decline':
                newStatus = media_1.MediaRequestStatus.DECLINED;
                break;
        }
        request.status = newStatus;
        request.modifiedBy = req.user;
        await requestRepository.save(request);
        return res.status(200).json(request);
    }
    catch (e) {
        logger_1.default.error('Error processing request update', {
            label: 'Media Request',
            message: e.message,
        });
        next({ status: 404, message: 'Request not found.' });
    }
});
exports.default = requestRoutes;
