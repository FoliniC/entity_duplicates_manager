(function () {
  "use strict";

  let now = Date.now();

  function hideCloudElement() {
    // Simple shadow DOM traversal
    function findInDOM(root) {
      if (!root) return null;

      // Look for the cloud element
      if (root.querySelectorAll) {
        const items = root.querySelectorAll('ha-md-list-item[type="link"]');
        for (let item of items) {
          if (
            item.textContent &&
            item.textContent.includes("Home Assistant Cloud")
          ) {
            return item;
          }
        }
      }

      // Recurse through shadow DOM
      if (root.children) {
        for (let child of root.children) {
          const found = findInDOM(child);
          if (found) return found;
        }
      }
      if (root.shadowRoot) {
        for (let child of root.shadowRoot.children) {
          const found = findInDOM(child);
          if (found) return found;
        }
      }

      return null;
    }

    const element = findInDOM(document.body);
    if (element && element.style.display !== "none") {
      // Just ONE reliable hiding method
      element.style.display = "none";
      const took = Date.now() - now;
      console.log(`HAC Cloud hidden! (took ${took} ms)`);

      return true;
    }
    return false;
  }

  function tryHideRepeatedly() {
    now = Date.now();
    hideCloudElement();
    setTimeout(hideCloudElement, 10);
    setTimeout(hideCloudElement, 30);
    setTimeout(hideCloudElement, 50);
    setTimeout(hideCloudElement, 100);
    setTimeout(hideCloudElement, 200);
    setTimeout(hideCloudElement, 500);
    setTimeout(hideCloudElement, 1500);
  }

  // Initial hide attempts
  tryHideRepeatedly();

  // Route change detection
  let currentPath = window.location.pathname;

  function checkForNavigation() {
    const newPath = window.location.pathname;
    if (newPath !== currentPath) {
      currentPath = newPath;

      tryHideRepeatedly();
    }
  }

  // Check for navigation every 300ms
  setInterval(checkForNavigation, 300);

  // Also listen for HA-specific events
  ["popstate", "click", "location-changed"].forEach((event) => {
    document.addEventListener(
      event,
      () => {
        tryHideRepeatedly();
      },
      true
    );
  });

  // Monitor for sidebar opening (HA often reloads sidebar content)
  const sidebarObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (
        mutation.type === "attributes" &&
        mutation.attributeName === "opened" &&
        mutation.target.tagName === "HA-DRAWER"
      ) {
        if (mutation.target.getAttribute("opened") === "true") {
          tryHideRepeatedly();
        }
      }
    });
  });

  sidebarObserver.observe(document.body, {
    attributes: true,
    attributeFilter: ["opened"],
    subtree: true,
  });

  //window.rehideCloud = hideCloudElement; // For manual testing
})();
