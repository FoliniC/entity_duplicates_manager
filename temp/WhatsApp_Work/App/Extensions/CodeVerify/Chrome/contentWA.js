(function () {
    'use strict';

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    const STATES = Object.freeze({
        // Starting state for all frames/tabs
        START: 'START',
        // Tab is processing scripts
        PROCESSING: 'PROCESSING',
        // Disable the extension (it shouldn't be running on this tab)
        IGNORE: 'IGNORE',
        // Script verification against the manifest failed.
        INVALID: 'INVALID',
        // Unknown inline script from an extension was found
        RISK: 'RISK',
        // All script verifications succeeded
        VALID: 'VALID',
        // Timed out waiting for the manifest to be available on the page
        TIMEOUT: 'TIMEOUT',
    });
    const ICONS = {
        DEFAULT: {
            32: 'default_32.png',
            64: 'default_64.png',
            128: 'default_128.png',
        },
        FAILURE: {
            32: 'failure_32.png',
        },
        RISK: {
            32: 'risk_32.png',
        },
        VALID: {
            32: 'validated_32.png',
        },
    };
    ({
        [STATES.START]: ICONS.DEFAULT,
        [STATES.PROCESSING]: ICONS.DEFAULT,
        [STATES.IGNORE]: ICONS.DEFAULT,
        [STATES.INVALID]: ICONS.FAILURE,
        [STATES.RISK]: ICONS.RISK,
        [STATES.VALID]: ICONS.VALID,
        [STATES.TIMEOUT]: ICONS.RISK,
    });
    const MESSAGE_TYPE = Object.freeze({
        DEBUG: 'DEBUG',
        LOAD_COMPANY_MANIFEST: 'LOAD_COMPANY_MANIFEST',
        POPUP_STATE: 'POPUP_STATE',
        RAW_SRC: 'RAW_SRC',
        UPDATE_STATE: 'UPDATE_STATE',
        STATE_UPDATED: 'STATE_UPDATED',
        CONTENT_SCRIPT_START: 'CONTENT_SCRIPT_START',
        UPDATED_CACHED_SCRIPT_URLS: 'UPDATED_CACHED_SCRIPT_URLS',
    });
    const ORIGIN_HOST = {
        FACEBOOK: 'facebook.com',
        WHATSAPP: 'whatsapp.com',
        MESSENGER: 'messenger.com',
        INSTAGRAM: 'instagram.com',
    };
    const ORIGIN_TYPE = Object.freeze({
        FACEBOOK: 'FACEBOOK',
        WHATSAPP: 'WHATSAPP',
        MESSENGER: 'MESSENGER',
        INSTAGRAM: 'INSTAGRAM',
    });
    // Firefox and Safari currently do not support CompressionStream/showSaveFilePicker
    const DOWNLOAD_SRC_ENABLED = 'CompressionStream' in window && 'showSaveFilePicker' in window;
    const MANIFEST_TIMEOUT = 45000;

    /******************************************************************************
    Copyright (c) Microsoft Corporation.

    Permission to use, copy, modify, and/or distribute this software for any
    purpose with or without fee is hereby granted.

    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
    REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
    AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
    INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
    LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
    OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
    PERFORMANCE OF THIS SOFTWARE.
    ***************************************************************************** */

    function __awaiter(thisArg, _arguments, P, generator) {
        function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
        return new (P || (P = Promise))(function (resolve, reject) {
            function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
            function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
            function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
            step((generator = generator.apply(thisArg, _arguments || [])).next());
        });
    }

    typeof SuppressedError === "function" ? SuppressedError : function (error, suppressed, message) {
        var e = new Error(message);
        return e.name = "SuppressedError", e.error = error, e.suppressed = suppressed, e;
    };

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function sendMessageToBackground(message, callback) {
        if (callback != null) {
            chrome.runtime.sendMessage(message, callback);
        }
        else {
            chrome.runtime.sendMessage(message);
        }
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    let currentOrigin;
    function setCurrentOrigin(origin) {
        currentOrigin = origin;
    }
    function getCurrentOrigin() {
        if (!currentOrigin) {
            invalidateAndThrow('Attemting to access currentOrigin before it has been set');
        }
        return currentOrigin;
    }
    function updateCurrentState(state, details) {
        if (state == STATES.INVALID) {
            logInvalidation(details);
        }
        sendMessageToBackground({
            type: MESSAGE_TYPE.UPDATE_STATE,
            state,
            origin: getCurrentOrigin(),
            details,
        });
    }
    function invalidateAndThrow(details) {
        updateCurrentState(STATES.INVALID, details);
        throw new Error(details);
    }

    function logInvalidation(details) {
        if (details == null) {
            return;
        }
        fetch(`https://web.whatsapp.com/bt_validation_result/__VALIDATION__RESULT__FILTER__NONCE__/${STATES.IGNORE}?details=${details}`).catch(() => { });
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function parseCSPString(csp) {
        const directiveStrings = csp.split(';').filter(Boolean);
        return directiveStrings.reduce((map, directiveString) => {
            const [directive, ...values] = directiveString
                .trim()
                .toLowerCase()
                .split(' ');
            // Ignore subsequent keys for a directive, if it's specified more than once
            if (!map.has(directive)) {
                map.set(directive, new Set(values));
            }
            return map;
        }, new Map());
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function alertBackgroundOfImminentFetch(url) {
        return new Promise(resolve => {
            sendMessageToBackground({
                type: MESSAGE_TYPE.UPDATED_CACHED_SCRIPT_URLS,
                url,
            }, () => {
                resolve();
            });
        });
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function scanForCSPEvalReportViolations() {
        document.addEventListener('securitypolicyviolation', e => {
            // Older Browser can't distinguish between 'eval' and 'wasm-eval' violations
            // We need to check if there is an eval violation
            if (e.blockedURI !== 'eval') {
                return;
            }
            if (e.disposition === 'enforce') {
                return;
            }
            alertBackgroundOfImminentFetch(e.sourceFile).then(() => {
                fetch(e.sourceFile)
                    .then(response => response.text())
                    .then(code => {
                    const violatingLine = code.split(/\r?\n/)[e.lineNumber - 1];
                    if (violatingLine.includes('WebAssembly') &&
                        !violatingLine.includes('eval(') &&
                        !violatingLine.includes('Function(') &&
                        !violatingLine.includes("setTimeout('") &&
                        !violatingLine.includes("setInterval('") &&
                        !violatingLine.includes('setTimeout("') &&
                        !violatingLine.includes('setInterval("')) {
                        return;
                    }
                    updateCurrentState(STATES.INVALID, `Caught eval in ${e.sourceFile}`);
                });
            });
        });
    }
    function getIsValidDefaultSrc$1(cspHeaders) {
        return cspHeaders.some(cspHeader => {
            const cspMap = parseCSPString(cspHeader);
            const defaultSrc = cspMap.get('default-src');
            const scriptSrc = cspMap.get('script-src');
            if (!scriptSrc && defaultSrc) {
                if (!defaultSrc.has("'unsafe-eval'")) {
                    return true;
                }
            }
            return false;
        });
    }
    function getIsValidScriptSrcAndHasScriptSrcDirective$1(cspHeaders) {
        let hasScriptSrcDirective = false;
        const isValidScriptSrc = cspHeaders.some(cspHeader => {
            const cspMap = parseCSPString(cspHeader);
            const scriptSrc = cspMap.get('script-src');
            if (scriptSrc) {
                hasScriptSrcDirective = true;
                if (!scriptSrc.has("'unsafe-eval'")) {
                    return true;
                }
            }
            return false;
        });
        return [isValidScriptSrc, hasScriptSrcDirective];
    }
    function checkCSPForEvals(cspHeaders, cspReportHeaders) {
        const [hasValidScriptSrcEnforcement, hasScriptSrcDirectiveForEnforce] = getIsValidScriptSrcAndHasScriptSrcDirective$1(cspHeaders);
        // 1. This means that at least one CSP-header declaration has a script-src
        // directive that has no `unsafe-eval` keyword. This means the browser will
        // enforce unsafe eval for us.
        if (hasValidScriptSrcEnforcement) {
            return [true];
        }
        // 2. If we have no script-src directives, the browser will fall back to
        // default-src. If at least one declaration has a default-src directive
        // with no `unsafe-eval`, the browser will enforce for us.
        if (!hasScriptSrcDirectiveForEnforce) {
            if (getIsValidDefaultSrc$1(cspHeaders)) {
                return [true];
            }
        }
        // If we've gotten this far, it either means something is invalid, or this is
        // an older browser. We want to execute WASM, but still prevent unsafe-eval.
        // Newer browsers support the wasm-unsafe-eval keyword for this purpose, but
        // for older browsers we need to hack around this.
        // The technique we're using here involves setting report-only headers that
        // match the rules we checked above, but for enforce headers. These will not
        // cause the page to break, but will emit events that we can listen for in
        // scanForCSPEvalReportViolations.
        // 3. Thus, if we've gotten this far and we have no report headers, the page
        // should be considered invalid.
        if (!cspReportHeaders || cspReportHeaders.length === 0) {
            return [false, 'Missing CSP report-only header'];
        }
        // Check if at least one header has the correct report setup
        // If CSP is not reporting on evals we cannot catch them via event listeners
        const [hasValidScriptSrcReport, hasScriptSrcDirectiveForReport] = getIsValidScriptSrcAndHasScriptSrcDirective$1(cspReportHeaders);
        let hasValidDefaultSrcReport = false;
        if (!hasScriptSrcDirectiveForReport) {
            hasValidDefaultSrcReport = getIsValidDefaultSrc$1(cspReportHeaders);
        }
        // 4. If neither
        //  a. We have at least one script-src without unsafe eval.
        //  b. We have no script-src, and at least one default-src without unsafe-eval
        // Then we must invalidate because there is nothing preventing unsafe-eval.
        if (!hasValidScriptSrcReport && !hasValidDefaultSrcReport) {
            return [false, 'Missing unsafe-eval from CSP report-only header'];
        }
        // 5. If we've gotten here without throwing, we can start scanning for violations
        // from our report-only headers.
        scanForCSPEvalReportViolations();
        return [true];
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    /**
     * Enforces that CSP headers do not allow unsafe-inline
     */
    function checkCSPForUnsafeInline(cspHeaders) {
        const preventsUnsafeInline = cspHeaders.some(cspHeader => {
            const headers = parseCSPString(cspHeader);
            const scriptSrc = headers.get('script-src');
            if (scriptSrc) {
                return !scriptSrc.has(`'unsafe-inline'`);
            }
            const defaultSrc = headers.get('default-src');
            if (defaultSrc) {
                return !defaultSrc.has(`'unsafe-inline'`);
            }
            return false;
        });
        if (preventsUnsafeInline) {
            return [true];
        }
        else {
            return [false, 'CSP Headers do not prevent unsafe-inline.'];
        }
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function checkCSPForWorkerSrc(cspHeaders, origin) {
        const host = ORIGIN_HOST[origin];
        const headersWithWorkerSrc = cspHeaders.filter(cspHeader => parseCSPString(cspHeader).has('worker-src'));
        if (headersWithWorkerSrc.length === 0) {
            return [false, 'Missing worker-src directive on CSP of main document'];
        }
        // Valid CSP if at least one CSP header is strict enough, since the browser
        // should apply all.
        const isValid = headersWithWorkerSrc.some(cspHeader => {
            const cspMap = parseCSPString(cspHeader);
            const workersSrcValues = cspMap.get('worker-src');
            return (workersSrcValues &&
                !workersSrcValues.has('data:') &&
                !workersSrcValues.has('blob:') &&
                !workersSrcValues.has("'self'") &&
                /**
                 * Ensure that worker-src doesn't have values like *.facebook.com
                 * this would require us to assume that every non main-thread script
                 * from this origin might be a worker setting us for potential breakages
                 * in the future. Instead worker-src should be a finite list of urls,
                 * which if fetched will be ensured to have valid CSPs within them,
                 * since url backed workers have independent CSP.
                 */
                !Array.from(workersSrcValues.values()).some(value => value.endsWith(host) || value.endsWith(host + '/')));
        });
        if (isValid) {
            return [true];
        }
        else {
            return [false, 'Invalid worker-src directive on main document'];
        }
    }
    function checkDocumentCSPHeaders(cspHeaders, cspReportHeaders, origin) {
        [
            checkCSPForUnsafeInline(cspHeaders),
            checkCSPForEvals(cspHeaders, cspReportHeaders),
            checkCSPForWorkerSrc(cspHeaders, origin),
        ].forEach(([valid, reason]) => {
            if (!valid) {
                invalidateAndThrow(reason);
            }
        });
    }
    function getAllowedWorkerCSPs(cspHeaders) {
        return cspHeaders
            .map(header => parseCSPString(header).get('worker-src'))
            .filter((header) => !!header);
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function parseFailedJSON(queuedJsonToParse) {
        var _a;
        // Only a document/doctype can have textContent as null
        const nodeTextContent = (_a = queuedJsonToParse.node.textContent) !== null && _a !== void 0 ? _a : '';
        try {
            JSON.parse(nodeTextContent);
        }
        catch (parseError) {
            if (queuedJsonToParse.retry > 0) {
                queuedJsonToParse.retry--;
                setTimeout(() => parseFailedJSON(queuedJsonToParse), 20);
            }
            else {
                updateCurrentState(STATES.INVALID);
            }
        }
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function isPathnameExcluded(excludedPathnames) {
        let pathname = location.pathname;
        if (!pathname.endsWith('/')) {
            pathname = pathname + '/';
        }
        return excludedPathnames.some(rule => {
            if (typeof rule === 'string') {
                return pathname === rule;
            }
            else {
                const match = pathname.match(rule);
                return match != null && match[0] === pathname;
            }
        });
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function doesWorkerUrlConformToCSP(workerValues, url) {
        // https://www.w3.org/TR/CSP3/#match-paths
        // *.facebook.com/sw/ -> does not exactMatch
        // *.facebook.com/sw -> needs exact match
        for (const value of workerValues) {
            const exactMatch = !value.endsWith('/');
            // Allowed query parameters for exact match, and everything for non exact match
            const regexEnd = exactMatch ? '(\\?*)?$' : '*$';
            const regex = new RegExp(('^' + value + regexEnd).replaceAll('*', '.*'));
            if (regex.test(url)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function getCSPHeadersFromWebRequestResponse(response, reportHeader = false) {
        const responseHeaders = response.responseHeaders;
        if (!responseHeaders) {
            throw new Error('Request is missing responseHeaders');
        }
        const cspHeaders = responseHeaders.filter(header => header.name.toLowerCase() ===
            (reportHeader
                ? 'content-security-policy-report-only'
                : 'content-security-policy'));
        // A single header value can be a comma seperated list of headers
        // https://www.w3.org/TR/CSP3/#parse-serialized-policy-list
        const individualHeaders = [];
        cspHeaders.forEach(header => {
            var _a;
            if ((_a = header.value) === null || _a === void 0 ? void 0 : _a.includes(', ')) {
                header.value.split(', ').forEach(headerValue => {
                    individualHeaders.push({ name: header.name, value: headerValue });
                });
            }
            else {
                individualHeaders.push(header);
            }
        });
        return individualHeaders;
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    /**
     * Dedicated Workers can nest workers, we need to check their CSPs.
     *
     * worker-src CSP inside a worker should conform to atleast
     * one of the worker-src CSPs on the main document which
     * have already been validated, otherwise worker can spin
     * up arbitrary workers or blob:/data:.
     */
    function isWorkerSrcValid(cspHeaders, host, documentWorkerCSPs) {
        return cspHeaders.some(header => {
            const allowedWorkers = parseCSPString(header).get('worker-src');
            if (allowedWorkers) {
                /**
                 * Filter out worker-src that aren't same origin because of the bellow bug
                 * This is safe to do since workers MUST be same-origin by definition
                 * https://bugzilla.mozilla.org/show_bug.cgi?id=1847548&fbclid=IwAR3qIyYr5K92_Cw3UJmgtSbgBKwZ5bLppP6LNwN6lC-kQVEdxr_52zeQUPE
                 */
                const allowedWorkersToCheck = Array.from(allowedWorkers.values()).filter(worker => worker.includes('.' + host) || worker.startsWith(host));
                return documentWorkerCSPs.some(documentWorkerValues => {
                    return allowedWorkersToCheck.every(workerSrcValue => doesWorkerUrlConformToCSP(documentWorkerValues, workerSrcValue) ||
                        documentWorkerValues.has(workerSrcValue));
                });
            }
            return false;
        });
    }
    /**
     * Check script-src for blob: data:
     * Workers can call importScripts/import on arbitrary strings.
     * This CSP should be in place to prevent that.
     */
    function areBlobAndDataExcluded(cspHeaders) {
        const [hasValidScriptSrcEnforcement, hasScriptSrcDirectiveForEnforce] = getIsValidScriptSrcAndHasScriptSrcDirective(cspHeaders);
        if (hasValidScriptSrcEnforcement) {
            return true;
        }
        if (!hasScriptSrcDirectiveForEnforce) {
            if (getIsValidDefaultSrc(cspHeaders)) {
                return true;
            }
        }
        return false;
    }
    /**
     * This function should not have side-effects (no throw, no invalidation).
     * See checkWorkerEndpointCSP for enforcement.
     */
    function isWorkerEndpointCSPValid(response, documentWorkerCSPs, origin) {
        const host = ORIGIN_HOST[origin];
        const cspHeaders = getCSPHeadersFromWebRequestResponse(response)
            .map(h => h.value)
            .filter((header) => !!header);
        const cspReportHeaders = getCSPHeadersFromWebRequestResponse(response, true)
            .map(h => h.value)
            .filter((header) => !!header);
        const [evalIsValid, evalReason] = checkCSPForEvals(cspHeaders, cspReportHeaders);
        if (!evalIsValid) {
            return [false, evalReason];
        }
        if (!isWorkerSrcValid(cspHeaders, host, documentWorkerCSPs)) {
            return [
                false,
                'Nested worker-src does not conform to document worker-src CSP',
            ];
        }
        if (!areBlobAndDataExcluded(cspHeaders)) {
            return [false, 'Worker allows blob:/data: importScripts/import'];
        }
        return [true];
    }
    function checkWorkerEndpointCSP(response, documentWorkerCSPs, origin) {
        const [valid, reason] = isWorkerEndpointCSPValid(response, documentWorkerCSPs, origin);
        if (!valid) {
            invalidateAndThrow(reason);
        }
    }
    function cspValuesExcludeBlobAndData(cspValues) {
        return !cspValues.has('blob:') && !cspValues.has('data:');
    }
    function getIsValidDefaultSrc(cspHeaders) {
        return cspHeaders.some(cspHeader => {
            const cspMap = parseCSPString(cspHeader);
            const defaultSrc = cspMap.get('default-src');
            if (!cspMap.has('script-src') && defaultSrc) {
                if (cspValuesExcludeBlobAndData(defaultSrc)) {
                    return true;
                }
            }
            return false;
        });
    }
    function getIsValidScriptSrcAndHasScriptSrcDirective(cspHeaders) {
        let hasScriptSrcDirective = false;
        const isValidScriptSrc = cspHeaders.some(cspHeader => {
            const cspMap = parseCSPString(cspHeader);
            const scriptSrc = cspMap.get('script-src');
            if (scriptSrc) {
                hasScriptSrcDirective = true;
                if (cspValuesExcludeBlobAndData(scriptSrc)) {
                    return true;
                }
            }
            return false;
        });
        return [isValidScriptSrc, hasScriptSrcDirective];
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function pushToOrCreateArrayInMap(outerMap, outerKey, value) {
        var _a;
        const innerArray = (_a = outerMap.get(outerKey)) !== null && _a !== void 0 ? _a : [];
        innerArray.push(value);
        if (!outerMap.has(outerKey)) {
            outerMap.set(outerKey, innerArray);
        }
        return outerMap;
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function ensureManifestWasOrWillBeLoaded(loadedVersions, version) {
        if (loadedVersions.has(version)) {
            return;
        }
        setTimeout(() => {
            if (!loadedVersions.has(version)) {
                updateCurrentState(STATES.INVALID, `Detected script from manifest version ${version} that has not been loaded`);
            }
        }, MANIFEST_TIMEOUT);
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    /**
     * Return text from the response object. The main purpose of this method is to
     * extract and parse sourceURL and sourceMappingURL comments from inlined data
     * scripts.
     * Note that this function consumes the response body!
     *
     * @param {Response} response Response will be consumed!
     * @returns string Response text if the sourceURL is valid
     */
    function genSourceText(response) {
        var _a;
        return __awaiter(this, void 0, void 0, function* () {
            const sourceText = yield response.text();
            // Just a normal script tag with a source url
            if (!response.url.startsWith('data:application/x-javascript')) {
                return sourceText;
            }
            // Inlined data-script. We need to extract with optional `//# sourceURL=` and
            // `//# sourceMappingURL=` comments before sending it over to be hashed...
            const sourceTextParts = sourceText.trimEnd().split('\n');
            // NOTE: For security reasons, we expect inlined data scripts to *end* with
            // sourceURL comments. This is because a man-in-the-middle can insert code
            // after the sourceURL comment, which would execute on the browser but get
            // stripped away by the extension before getting hashed + verified.
            // As a result, we're always starting our search from the bottom.
            const lastPart = sourceTextParts[sourceTextParts.length - 1];
            if (lastPart.startsWith('//# sourceURL=')) {
                sourceTextParts.pop();
                const sourceURL = (_a = lastPart.split('//# sourceURL=')[1]) !== null && _a !== void 0 ? _a : '';
                if (!sourceURL.startsWith('http')) {
                    throw new Error(`Invalid sourceUrl in inlined data script: ${sourceURL}`);
                }
            }
            while (sourceTextParts[sourceTextParts.length - 1] === '\n' ||
                sourceTextParts[sourceTextParts.length - 1].startsWith('//# sourceMappingURL=')) {
                sourceTextParts.pop();
            }
            return sourceTextParts.join('\n').trim();
        });
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function downloadArchive(sourceScripts) {
        return __awaiter(this, void 0, void 0, function* () {
            const fileHandle = yield window.showSaveFilePicker({
                suggestedName: 'meta_source_files.gz',
            });
            const writableStream = yield fileHandle.createWritable();
            // delimiter between files
            const delimPrefix = '\n********** new file: ';
            const delimSuffix = ' **********\n';
            const enc = new TextEncoder();
            for (const [fileName, compressedStream] of sourceScripts.entries()) {
                const delim = delimPrefix + fileName + delimSuffix;
                const encodedDelim = enc.encode(delim);
                const delimStream = new window.CompressionStream('gzip');
                const writer = delimStream.writable.getWriter();
                writer.write(encodedDelim);
                writer.close();
                yield delimStream.readable.pipeTo(writableStream, { preventClose: true });
                yield compressedStream.pipeTo(writableStream, { preventClose: true });
            }
            writableStream.close();
        });
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    const SOURCE_SCRIPTS_AND_STYLES = new Map();
    function processSrc(tagDetails, version) {
        return __awaiter(this, void 0, void 0, function* () {
            try {
                let packages = [];
                if (tagDetails.type === 'script' || tagDetails.type === 'link') {
                    // fetch the script/style from page context, not the extension context.
                    const url = tagDetails.type === 'script' ? tagDetails.src : tagDetails.href;
                    const isServiceWorker = tagDetails.type === 'script' && tagDetails.isServiceWorker;
                    yield alertBackgroundOfImminentFetch(url);
                    const sourceResponse = yield fetch(url, {
                        method: 'GET',
                        // When the browser fetches a service worker it adds this header.
                        // If this is missing it will cause a cache miss, resulting in invalidation.
                        headers: isServiceWorker ? { 'Service-Worker': 'script' } : undefined,
                    });
                    if (DOWNLOAD_SRC_ENABLED) {
                        const fileNameArr = url.split('/');
                        const fileName = fileNameArr[fileNameArr.length - 1].split('?')[0];
                        const responseBody = sourceResponse.clone().body;
                        if (!responseBody) {
                            throw new Error('Response for fetched script has no body');
                        }
                        SOURCE_SCRIPTS_AND_STYLES.set(fileName, responseBody.pipeThrough(new window.CompressionStream('gzip')));
                    }
                    const sourceText = yield genSourceText(sourceResponse);
                    // split package up if necessary
                    packages = sourceText.split('/*FB_PKG_DELIM*/\n');
                }
                else if (tagDetails.type === 'style') {
                    packages = [tagDetails.tag.innerHTML];
                }
                const packagePromises = packages.map(pkg => {
                    return new Promise((resolve, reject) => {
                        sendMessageToBackground({
                            type: MESSAGE_TYPE.RAW_SRC,
                            pkgRaw: pkg.trimStart(),
                            origin: getCurrentOrigin(),
                            version: version,
                        }, response => {
                            if (response.valid) {
                                resolve(null);
                            }
                            else {
                                reject(response.reason);
                            }
                        });
                    });
                });
                yield Promise.all(packagePromises);
                return { valid: true };
            }
            catch (scriptProcessingError) {
                return {
                    valid: false,
                    type: scriptProcessingError,
                };
            }
        });
    }
    function downloadSrc() {
        downloadArchive(SOURCE_SCRIPTS_AND_STYLES);
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function hasVaryServiceWorkerHeader(response) {
        var _a;
        return (((_a = response.responseHeaders) === null || _a === void 0 ? void 0 : _a.find(header => {
            var _a;
            return header.name.includes('vary') &&
                ((_a = header.value) === null || _a === void 0 ? void 0 : _a.includes('Service-Worker'));
        })) !== undefined);
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function isTopWindow() {
        return window == window.top;
    }
    function isSameDomainAsTopWindow() {
        var _a;
        try {
            // This is inside a try/catch because even attempting to access the `origin`
            // property will throw a SecurityError if the domains don't match.
            return window.location.origin === ((_a = window.top) === null || _a === void 0 ? void 0 : _a.location.origin);
        }
        catch (_b) {
            return false;
        }
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    function getTagIdentifier(tagDetails) {
        switch (tagDetails.type) {
            case 'script':
                return tagDetails.src;
            case 'link':
                return tagDetails.href;
            case 'style':
                return 'style_' + tagDetails.tag.innerHTML.substring(0, 100);
        }
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    const BOTH = 'BOTH';
    function getManifestVersionAndTypeFromNode(element) {
        const versionAndType = tryToGetManifestVersionAndTypeFromNode(element);
        if (!versionAndType) {
            invalidateAndThrow(`Missing manifest data attribute or invalid version/typeon attribute`);
        }
        return versionAndType;
    }
    function tryToGetManifestVersionAndTypeFromNode(element) {
        const dataBtManifest = element.getAttribute('data-btmanifest');
        if (dataBtManifest == null) {
            return null;
        }
        // Scripts may contain packages from both main and longtail manifests,
        // e.g. "1009592080_main,1009592080_longtail"
        const [manifest1, manifest2] = dataBtManifest.split(',');
        // If this scripts contains packages from both main and longtail manifests
        // then require both manifests to be loaded before processing this script,
        // otherwise use the single type specified.
        const otherType = manifest2 ? BOTH : manifest1.split('_')[1];
        // It is safe to assume a script will not contain packages from different
        // versions, so we can use the first manifest version as the script version.
        const version = manifest1.split('_')[0];
        if (!version || !otherType) {
            return null;
        }
        return [version, otherType];
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    const CHECKED_STYLESHEET_HASHES = new Set();
    function scanForCSSNeedingManualInspsection() {
        checkForStylesheetChanges();
        setInterval(checkForStylesheetChanges, 1000);
    }
    function checkForStylesheetChanges() {
        return __awaiter(this, void 0, void 0, function* () {
            [...document.styleSheets, ...document.adoptedStyleSheets].forEach((sheet) => __awaiter(this, void 0, void 0, function* () {
                const potentialOwnerNode = sheet.ownerNode;
                if (sheet.href && potentialOwnerNode instanceof HTMLLinkElement) {
                    // Link style tags are checked agains the manifest
                    return;
                }
                if (potentialOwnerNode instanceof HTMLStyleElement &&
                    tryToGetManifestVersionAndTypeFromNode(potentialOwnerNode) != null) {
                    // Inline style covered by the main checks
                    return;
                }
                updateStateOnInvalidStylesheet(yield checkIsStylesheetValid(sheet), sheet);
            }));
        });
    }
    function checkIsStylesheetValid(styleSheet) {
        var _a;
        return __awaiter(this, void 0, void 0, function* () {
            const potentialOwnerNode = styleSheet.ownerNode;
            if (potentialOwnerNode instanceof HTMLStyleElement) {
                const hashedContent = yield hashString((_a = potentialOwnerNode.textContent) !== null && _a !== void 0 ? _a : '');
                if (CHECKED_STYLESHEET_HASHES.has(hashedContent)) {
                    return true;
                }
                CHECKED_STYLESHEET_HASHES.add(hashedContent);
            }
            // We have to look at every CSS rule
            return [...styleSheet.cssRules].every(isValidCSSRule);
        });
    }
    function isValidCSSRule(rule) {
        if (rule instanceof CSSKeyframeRule &&
            rule.style.getPropertyValue('font-family') !== '') {
            // Attempting to animate fonts
            return false;
        }
        if (!(rule instanceof CSSGroupingRule ||
            rule instanceof CSSKeyframesRule ||
            rule instanceof CSSImportRule)) {
            return true;
        }
        let rulesToCheck = [];
        if (rule instanceof CSSImportRule) {
            const styleSheet = rule.styleSheet;
            if (styleSheet != null) {
                ensureCORSEnabledForStylesheet(styleSheet);
                rulesToCheck = [...styleSheet.cssRules];
            }
        }
        else {
            rulesToCheck = [...rule.cssRules];
        }
        return rulesToCheck.every(isValidCSSRule);
    }
    function ensureCORSEnabledForStylesheet(styleSheet) {
        try {
            // Ensure all non same origin stylesheets can be accessed (CORS)
            styleSheet.cssRules;
        }
        catch (e) {
            updateStateOnInvalidStylesheet(false, styleSheet);
        }
    }
    function hashString(content) {
        return __awaiter(this, void 0, void 0, function* () {
            const text = new TextEncoder().encode(content);
            const hashBuffer = yield crypto.subtle.digest('SHA-256', text);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            return hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');
        });
    }
    function updateStateOnInvalidStylesheet(isValid, sheet) {
        var _a;
        if (!isValid) {
            const potentialHref = (_a = sheet.href) !== null && _a !== void 0 ? _a : '';
            updateCurrentState(STATES.INVALID, `Violating CSS stylesheet ${potentialHref}`);
        }
    }

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    let originConfig = null;
    const UNINITIALIZED = 'UNINITIALIZED';
    let currentFilterType = UNINITIALIZED;
    // Map<version, Array<TagDetails>>
    const FOUND_ELEMENTS = new Map([
        [UNINITIALIZED, []],
    ]);
    const ALL_FOUND_TAGS_URLS = new Set();
    const FOUND_MANIFEST_VERSIONS = new Set();
    let manifestTimeoutID = '';
    function handleManifestNode(manifestNode) {
        var _a, _b;
        if (manifestNode.getAttribute('type') !== 'application/json') {
            updateCurrentState(STATES.INVALID, 'Manifest script type is invalid');
            return;
        }
        let rawManifest = null;
        // Only a document/doctype can have textContent as null
        const manifestNodeTextContent = (_a = manifestNode.textContent) !== null && _a !== void 0 ? _a : '';
        try {
            rawManifest = JSON.parse(manifestNodeTextContent);
        }
        catch (manifestParseError) {
            setTimeout(() => parseFailedJSON({ node: manifestNode, retry: 5000 }), 20);
            return;
        }
        if (rawManifest == null || typeof rawManifest !== 'object') {
            invalidateAndThrow('Manifest is null');
        }
        const leaves = rawManifest.manifest;
        const otherHashes = rawManifest.manifest_hashes;
        const roothash = otherHashes.combined_hash;
        let otherType = '';
        let version = '';
        const maybeManifestType = manifestNode.getAttribute('data-manifest-type');
        if (maybeManifestType === null) {
            updateCurrentState(STATES.INVALID, 'manifest is missing `data-manifest-type` prop');
        }
        else {
            otherType = maybeManifestType;
        }
        const maybeManifestRev = manifestNode.getAttribute('data-manifest-rev');
        if (maybeManifestRev === null) {
            updateCurrentState(STATES.INVALID, 'manifest is missing `data-manifest-rev` prop');
        }
        else {
            version = maybeManifestRev;
        }
        // If this is the first manifest we've found, start processing scripts for
        // that type. If we have encountered a second manifest, we can assume both
        // main and longtail manifests are present.
        if (currentFilterType === UNINITIALIZED) {
            currentFilterType = otherType;
        }
        else {
            currentFilterType = BOTH;
        }
        const messagePayload = {
            type: MESSAGE_TYPE.LOAD_COMPANY_MANIFEST,
            leaves,
            origin: getCurrentOrigin(),
            otherHashes: otherHashes,
            rootHash: roothash,
            workaround: manifestNode.innerHTML,
            version,
        };
        // now that we know the actual version of the scripts, transfer the ones we know about.
        // also set the correct manifest type, "otherType" for already collected scripts
        const foundElementsWithoutVersion = FOUND_ELEMENTS.get(UNINITIALIZED);
        if (foundElementsWithoutVersion) {
            const elementsWithUpdatedType = foundElementsWithoutVersion.map(element => (Object.assign(Object.assign({}, element), { otherType: currentFilterType })));
            FOUND_ELEMENTS.set(version, [
                ...elementsWithUpdatedType,
                ...((_b = FOUND_ELEMENTS.get(version)) !== null && _b !== void 0 ? _b : []),
            ]);
            FOUND_ELEMENTS.delete(UNINITIALIZED);
        }
        else if (!FOUND_ELEMENTS.has(version)) {
            // New version is being loaded in
            FOUND_ELEMENTS.set(version, []);
        }
        sendMessageToBackground(messagePayload, response => {
            // then start processing its JS/CSS
            if (response.valid) {
                if (manifestTimeoutID !== '') {
                    clearTimeout(manifestTimeoutID);
                    manifestTimeoutID = '';
                }
                FOUND_MANIFEST_VERSIONS.add(version);
                window.setTimeout(() => processFoundElements(version), 0);
            }
            else {
                if ('UNKNOWN_ENDPOINT_ISSUE' === response.reason) {
                    updateCurrentState(STATES.TIMEOUT);
                    return;
                }
                updateCurrentState(STATES.INVALID);
            }
        });
    }
    const processFoundElements = (version) => __awaiter(void 0, void 0, void 0, function* () {
        const elementsForVersion = FOUND_ELEMENTS.get(version);
        if (!elementsForVersion) {
            invalidateAndThrow(`attempting to process elements for nonexistent version ${version}`);
        }
        const elements = elementsForVersion.splice(0).filter(element => {
            if (element.otherType === currentFilterType ||
                [BOTH, UNINITIALIZED].includes(currentFilterType)) {
                return true;
            }
            else {
                elementsForVersion.push(element);
            }
        });
        let pendingElementCount = elements.length;
        for (const element of elements) {
            yield processSrc(element, version).then(response => {
                const tagIdentifier = getTagIdentifier(element);
                pendingElementCount--;
                if (response.valid) {
                    if (pendingElementCount == 0) {
                        updateCurrentState(STATES.VALID);
                    }
                }
                else {
                    updateCurrentState(STATES.INVALID, `Invalid Tag ${tagIdentifier}`);
                }
                sendMessageToBackground({
                    type: MESSAGE_TYPE.DEBUG,
                    log: 'processed SRC response is ' +
                        JSON.stringify(response).substring(0, 500),
                    src: tagIdentifier,
                });
            });
        }
        window.setTimeout(() => processFoundElements(version), 3000);
    });
    function handleScriptNode(scriptNode) {
        const [version, otherType] = getManifestVersionAndTypeFromNode(scriptNode);
        ALL_FOUND_TAGS_URLS.add(scriptNode.src);
        ensureManifestWasOrWillBeLoaded(FOUND_MANIFEST_VERSIONS, version);
        pushToOrCreateArrayInMap(FOUND_ELEMENTS, version, {
            src: scriptNode.src,
            otherType,
            type: 'script',
        });
        updateCurrentState(STATES.PROCESSING);
    }
    function handleStyleNode(style) {
        const versionAndOtherType = tryToGetManifestVersionAndTypeFromNode(style);
        if (versionAndOtherType == null) {
            // Will be handled by manualCSSInspector
            return;
        }
        const [version, otherType] = versionAndOtherType;
        ensureManifestWasOrWillBeLoaded(FOUND_MANIFEST_VERSIONS, version);
        pushToOrCreateArrayInMap(FOUND_ELEMENTS, version, {
            tag: style,
            otherType: otherType,
            type: 'style',
        });
        updateCurrentState(STATES.PROCESSING);
    }
    function handleLinkNode(link) {
        const [version, otherType] = getManifestVersionAndTypeFromNode(link);
        ALL_FOUND_TAGS_URLS.add(link.href);
        ensureManifestWasOrWillBeLoaded(FOUND_MANIFEST_VERSIONS, version);
        pushToOrCreateArrayInMap(FOUND_ELEMENTS, version, {
            href: link.href,
            otherType,
            type: 'link',
        });
        updateCurrentState(STATES.PROCESSING);
    }
    function storeFoundElement(element) {
        var _a;
        if (!isTopWindow() && isSameDomainAsTopWindow()) {
            // this means that content utils is running in an iframe - disable timer and call processFoundElements on manifest processed in top level frame
            clearTimeout(manifestTimeoutID);
            manifestTimeoutID = '';
            FOUND_ELEMENTS.forEach((_val, key) => {
                window.setTimeout(() => processFoundElements(key), 0);
            });
        }
        // check if it's the manifest node
        if ((isTopWindow() || !isSameDomainAsTopWindow()) &&
            (element.id === 'binary-transparency-manifest' ||
                element.getAttribute('name') === 'binary-transparency-manifest')) {
            handleManifestNode(element);
        }
        // Only a document/doctype can have textContent as null
        const nodeTextContent = (_a = element.textContent) !== null && _a !== void 0 ? _a : '';
        if (element.getAttribute('type') === 'application/json') {
            try {
                JSON.parse(nodeTextContent);
            }
            catch (parseError) {
                setTimeout(() => parseFailedJSON({ node: element, retry: 1500 }), 20);
            }
            return;
        }
        if (element.nodeName.toLowerCase() === 'script') {
            const script = element;
            if (script.src != null &&
                script.src !== '' &&
                script.src.indexOf('blob:') === 0) {
                // TODO: try to process the blob. For now, flag as warning.
                updateCurrentState(STATES.INVALID, 'blob: src');
                return;
            }
            if (script.src !== '') {
                handleScriptNode(script);
            }
        }
        else if (element.nodeName.toLowerCase() === 'style') {
            const style = element;
            if (style.innerHTML !== '') {
                handleStyleNode(style);
            }
        }
        else if (element.nodeName.toLowerCase() === 'link') {
            handleLinkNode(element);
        }
    }
    function hasInvalidScriptsOrStyles(scriptNodeMaybe) {
        // if not an HTMLElement ignore it!
        if (scriptNodeMaybe.nodeType !== Node.ELEMENT_NODE) {
            return;
        }
        const nodeName = scriptNodeMaybe.nodeName.toLowerCase();
        if (nodeName === 'script' ||
            nodeName === 'style' ||
            (nodeName === 'link' &&
                scriptNodeMaybe.getAttribute('rel') == 'stylesheet')) {
            storeFoundElement(scriptNodeMaybe);
        }
        else if (scriptNodeMaybe.childNodes.length > 0) {
            scriptNodeMaybe.childNodes.forEach(childNode => {
                hasInvalidScriptsOrStyles(childNode);
            });
        }
    }
    const scanForScriptsAndStyles = () => {
        const allElements = document.querySelectorAll('script,style,link[rel="stylesheet"]');
        Array.from(allElements).forEach(element => {
            storeFoundElement(element);
        });
        try {
            // track any new tags that get loaded in
            const mutationObserver = new MutationObserver(mutationsList => {
                mutationsList.forEach(mutation => {
                    if (mutation.type === 'childList') {
                        Array.from(mutation.addedNodes).forEach(node => {
                            // Code within a script or style tag has changed
                            const targetNodeName = mutation.target.nodeName.toLocaleLowerCase();
                            if (node.nodeType === Node.TEXT_NODE &&
                                (targetNodeName === 'script' || targetNodeName === 'style')) {
                                hasInvalidScriptsOrStyles(mutation.target);
                            }
                            else {
                                hasInvalidScriptsOrStyles(node);
                            }
                        });
                    }
                });
            });
            mutationObserver.observe(document, {
                attributes: true,
                childList: true,
                subtree: true,
            });
        }
        catch (_UnknownError) {
            updateCurrentState(STATES.INVALID, 'unknown');
        }
    };
    let isUserLoggedIn = false;
    let allowedWorkerCSPs = [];
    function startFor(origin, config) {
        originConfig = config;
        setCurrentOrigin(origin);
        sendMessageToBackground({
            type: MESSAGE_TYPE.CONTENT_SCRIPT_START,
            origin,
        }, resp => {
            if (!resp.cspHeaders) {
                invalidateAndThrow('Expected CSP Headers in CONTENT_SCRIPT_START response');
            }
            checkDocumentCSPHeaders(resp.cspHeaders, resp.cspReportHeaders, getCurrentOrigin());
            allowedWorkerCSPs = getAllowedWorkerCSPs(resp.cspHeaders);
        });
        if (isPathnameExcluded(originConfig.excludedPathnames)) {
            updateCurrentState(STATES.IGNORE);
            return;
        }
        if (originConfig.checkLoggedInFromCookie) {
            // ds_user_id / c_user contains the user id of the user logged in
            const cookieName = origin === ORIGIN_TYPE.INSTAGRAM ? 'ds_user_id' : 'c_user';
            const cookies = document.cookie.split(';');
            cookies.forEach(cookie => {
                const pair = cookie.split('=');
                if (pair[0].indexOf(cookieName) >= 0) {
                    isUserLoggedIn = true;
                }
            });
        }
        else {
            // only doing this check for FB, MSGR, and IG
            isUserLoggedIn = true;
        }
        if (isUserLoggedIn) {
            updateCurrentState(STATES.PROCESSING);
            scanForScriptsAndStyles();
            scanForCSSNeedingManualInspsection();
            // set the timeout once, in case there's an iframe and contentUtils sets another manifest timer
            if (manifestTimeoutID === '') {
                manifestTimeoutID = window.setTimeout(() => {
                    // Manifest failed to load, flag a warning to the user.
                    updateCurrentState(STATES.TIMEOUT);
                }, MANIFEST_TIMEOUT);
            }
        }
    }
    chrome.runtime.onMessage.addListener(request => {
        if (request.greeting === 'validation_state') {
            fetch(`https://web.whatsapp.com/bt_validation_result/__VALIDATION__RESULT__FILTER__NONCE__/${request.state}`).catch(()=>{});
        }
        if (request.greeting === 'downloadSource' && DOWNLOAD_SRC_ENABLED) {
            downloadSrc();
        }
        else if (request.greeting === 'nocacheHeaderFound') {
            updateCurrentState(STATES.INVALID, `Detected uncached script/style ${request.uncachedUrl}`);
        }
        else if (request.greeting === 'checkIfScriptWasProcessed') {
            if (isUserLoggedIn && !ALL_FOUND_TAGS_URLS.has(request.response.url)) {
                const hostname = window.location.hostname;
                const resourceURL = new URL(request.response.url);
                if (resourceURL.hostname === hostname) {
                    // This can potentially be a worker, check if CSPs allow it as a worker
                    if (allowedWorkerCSPs.every(csp => doesWorkerUrlConformToCSP(csp, resourceURL.toString()))) {
                        // This might be a worker, ensure it's CSP headers are valid
                        checkWorkerEndpointCSP(request.response, allowedWorkerCSPs, getCurrentOrigin());
                    }
                }
                sendMessageToBackground({
                    type: MESSAGE_TYPE.DEBUG,
                    log: `Tab is processing ${request.response.url}`,
                });
                ALL_FOUND_TAGS_URLS.add(request.response.url);
                const uninitializedScripts = FOUND_ELEMENTS.get(FOUND_ELEMENTS.keys().next().value);
                if (uninitializedScripts) {
                    uninitializedScripts.push({
                        src: request.response.url,
                        otherType: currentFilterType,
                        isServiceWorker: hasVaryServiceWorkerHeader(request.response),
                        type: 'script',
                    });
                }
                updateCurrentState(STATES.PROCESSING);
            }
        }
        else if (request.greeting === 'sniffableMimeTypeResource') {
            updateCurrentState(STATES.INVALID, `Sniffable MIME type resource: ${request.src}`);
        }
        else if (request.greeting === 'downloadReleaseSource') {
            for (const key of FOUND_ELEMENTS.keys()) {
                if (key !== 'UNINITIALIZED') {
                    window.open(`https://www.facebook.com/btarchive/${key}/${getCurrentOrigin().toLowerCase()}`, '_blank', 'noopener,noreferrer');
                }
            }
        }
    });

    /**
     * Copyright (c) Meta Platforms, Inc. and affiliates.
     *
     * This source code is licensed under the MIT license found in the
     * LICENSE file in the root directory of this source tree.
     */
    startFor(ORIGIN_TYPE.WHATSAPP, {
        checkLoggedInFromCookie: false,
        excludedPathnames: [],
    });

})();
