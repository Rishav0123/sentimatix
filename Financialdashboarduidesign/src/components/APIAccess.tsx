import React from "react";

export function APIAccess(): JSX.Element {
  const apiKey = import.meta.env.VITE_API_KEY || "";

  return (
    <div className="p-6">
      <h3 className="text-lg text-white mb-2">API Access</h3>
      {apiKey ? (
        <div className="text-sm text-gray-300">API key is configured via environment variables.</div>
      ) : (
        <div className="text-sm text-yellow-300">No API key found. Configure `VITE_API_KEY` in your environment (.env) to enable API features.</div>
      )}
    </div>
  );
}

export default APIAccess;
