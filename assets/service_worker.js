/**
 * The code below is given by MDN.
 */

const cache_name = "v1";

const addResourcesToCache = async (resources) => {
    const cache = await caches.open(cache_name);
    await cache.addAll(resources);
};

const putInCache = async (request, response) => {
    const cache = await caches.open(cache_name);
    await cache.put(request, response);
};

const cacheFirst = async ({request, preloadResponsePromise, fallbackUrl}) => {
    const responseFromCache = await caches.match(request);
    console.log("Calling Service Worker Cache First Method: ", request);
    if (responseFromCache) {
        return responseFromCache;
    }
    const preloadResponse = await preloadResponsePromise;
    if (preloadResponse){
        console.log("using preload response", preloadResponse);
        putInCache(request, preloadResponse.clone());
        return preloadResponse;
    }
    try{
        const responseFromNetwork = await fetch(request);
        putInCache(request, responseFromNetwork.clone());
        return responseFromNetwork;
    }catch(error){
        const fallbackResponse = await caches.match(fallbackUrl);
        if (fallbackResponse){
            return fallbackResponse;
        }
        return new Response("Network error happened", {
            status: 408,
            headers: {"Content-Type":"text/plain"}
        })
    }
};

const enableNavigationPreload = async() => {
    if(self.registration.navigationPreload){
        await self.registration.navigationPreload.enable();
    }
};

self.addEventListener("activate", (event)=> {
    event.waitUntil(enableNavigationPreload());
});

self.addEventListener("install", (event)=>{
    event.waitUntil(addResourcesToCache([
        "/",
        "/about/"
    ]));
});

self.addEventListener("fetch", (event)=>{
    console.log(event);
    event.respondWith(cacheFirst({
        request: event.request,
        preloadResponsePromise: event.preloadResponse,
        fallbackUrl: "/about/"
    }));
});
