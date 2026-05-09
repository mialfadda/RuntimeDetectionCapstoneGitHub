import { useState, useEffect } from 'react';

export default function Extension() {
  const [progress, setProgress] = useState(0);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (done) return;
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setDone(true);
          return 100;
        }
        return prev + 2;
      });
    }, 60);
    return () => clearInterval(interval);
  }, [done]);

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center bg-white px-6">
      <div className="w-full max-w-lg text-center">
        {!done ? (
          <>
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-[#dde6f5] flex items-center justify-center">
              <svg className="w-10 h-10 text-[#2D5FA6] animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-[#1A3A6B] mb-4">Installing Extension...</h2>
            <div className="w-full bg-gray-200 rounded-full h-3 mb-3 overflow-hidden">
              <div className="bg-[#2D5FA6] h-3 rounded-full transition-all duration-100" style={{ width: `${progress}%` }} />
            </div>
            <p className="text-sm text-gray-500">{progress}%</p>
          </>
        ) : (
          <>
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-green-100 flex items-center justify-center">
              <svg className="w-10 h-10 text-[#22c55e]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-[#22c55e] mb-4">Extension Installed Successfully!</h2>
            <p className="text-gray-500 text-sm mb-8">Follow these steps to load it in Chrome:</p>

            {/* Install instructions */}
            <div className="text-left bg-gray-50 rounded-xl p-6 space-y-5">
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-[#2D5FA6] text-white flex items-center justify-center font-bold text-sm shrink-0">1</div>
                <div>
                  <h3 className="font-semibold text-[#1A3A6B] text-sm">Enable Developer Mode</h3>
                  <p className="text-gray-500 text-xs mt-1">
                    Open <code className="bg-gray-200 px-1 rounded text-xs">chrome://extensions</code> and toggle <strong>Developer mode</strong> in the top right corner.
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-[#2D5FA6] text-white flex items-center justify-center font-bold text-sm shrink-0">2</div>
                <div>
                  <h3 className="font-semibold text-[#1A3A6B] text-sm">Load Unpacked</h3>
                  <p className="text-gray-500 text-xs mt-1">
                    Click <strong>"Load unpacked"</strong> in the top left.
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-[#2D5FA6] text-white flex items-center justify-center font-bold text-sm shrink-0">3</div>
                <div>
                  <h3 className="font-semibold text-[#1A3A6B] text-sm">Select extension/ folder</h3>
                  <p className="text-gray-500 text-xs mt-1">
                    Navigate to the project root and select the <code className="bg-gray-200 px-1 rounded text-xs">extension/</code> folder.
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
