
  import { createRoot } from "react-dom/client";
  import App from "./App.tsx";
  import "./index.css";

  // Safety-net fetch wrapper to normalize duplicated '/api/api' segments in URLs
  // This prevents broken requests if VITE_API_URL is set with a trailing '/api'
  (function() {
    try {
      const originalFetch = window.fetch.bind(window);
      window.fetch = (input: RequestInfo, init?: RequestInit) => {
        let url = input as any;
        let isRequest = false;
        if (input instanceof Request) {
          isRequest = true;
          url = input.url;
        }
        if (typeof url === 'string') {
          const normalized = url.replace(/\/api\/api\//g, '/api/');
          if (isRequest) {
            input = new Request(normalized, input as Request);
          } else {
            input = normalized;
          }
        }
        return originalFetch(input, init);
      };
    } catch (e) {
      // Ignore if the environment doesn't allow overriding fetch
      console.warn('Fetch wrapper failed to initialize', e);
    }
  })();

  createRoot(document.getElementById("root")!).render(<App />);
  