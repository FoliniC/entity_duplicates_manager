const allowedZoomFactors = [0.8, 0.9, 1, 1.1, 1.25, 1.35, 1.5];
const DefaulZoomFactor = 1;
const storageKey = "current-zoom-factor";

chrome.runtime.onMessageExternal.addListener(
    function (request, _, sendResponse) {
        handleMessage(request, sendResponse);

        return true;
    }
);

const getNewZoomFactor = (zoom, isZoomIn) => {
    const index = isZoomIn
        ? allowedZoomFactors.findIndex(factor => zoom < factor)
        : allowedZoomFactors.findLastIndex(factor => zoom > factor);
    return (index === -1 ? zoom : allowedZoomFactors.at(index)) ?? zoom;
};

const setZoom = async (newZoom, tabId) => {
    if (tabId == null) {
        await chrome.tabs.setZoom(newZoom);
    } else {
        await chrome.tabs.setZoom(tabId, newZoom);
    }
    
    await chrome.storage.local.set({ [storageKey]: newZoom })
}

const getZoomFactor = async () => (await chrome.storage.local.get([storageKey]))[storageKey] ?? DefaulZoomFactor;

const handleMessage = async (request, sendResponse) => {
    if (request.type === "zoom-in") {
        const zoom = await getZoomFactor();
        const newZoom = getNewZoomFactor(zoom, true);
        await setZoom(newZoom);
        sendResponse({ zoom: newZoom });
    } else if (request.type === "zoom-out") {
        const zoom = await getZoomFactor();
        const newZoom = getNewZoomFactor(zoom, false);
        await setZoom(newZoom);
        sendResponse({ zoom: newZoom });
    } else if (request.type === "zoom-reset") {
        const zoom = DefaulZoomFactor;
        await setZoom(zoom);
        sendResponse({ zoom });
    } else if (request.type === "set-zoom") {
        const zoom = request.zoom;
        await setZoom(zoom);
        sendResponse({ zoom });
    } else if (request.type === "get-zoom") {
        const zoom = await getZoomFactor();
        sendResponse({ zoom });
    }
};

const handleUpdated = async (tabId, _, tab) => {
    if (tab.url && tab.url.startsWith("http")) {
        const zoom = await getZoomFactor();
        await setZoom(zoom, tabId);
    }
}

chrome.tabs.onUpdated.addListener(handleUpdated); 