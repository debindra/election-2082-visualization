import React from 'react';
import { getLegalContent } from '../config/legalContent';

/**
 * Renders markdown-like text: ## heading, **bold**, [text](url)
 */
function renderBlock(line, index) {
  const trimmed = line.trim();
  if (!trimmed) return null;
  if (trimmed.startsWith('## ')) {
    return React.createElement('h2', { key: index, className: 'text-lg font-semibold text-[#1e3a5f] mt-4 mb-2 first:mt-0' }, parseInline(trimmed.slice(3)));
  }
  const parts = parseInline(trimmed);
  return React.createElement('p', { key: index, className: 'text-[#1e3a5f]/90 text-sm leading-relaxed mb-2' }, parts);
}

function parseInline(text) {
  const out = [];
  let rest = text;
  while (rest.length > 0) {
    const bold = rest.match(/\*\*([^*]+)\*\*/);
    const link = rest.match(/\[([^\]]+)\]\((https?:[^)]+)\)/);
    if (link && (!bold || rest.indexOf(link[0]) <= rest.indexOf(bold[0]))) {
      const before = rest.slice(0, rest.indexOf(link[0]));
      if (before) out.push(before);
      out.push(React.createElement('a', { key: out.length, href: link[2], target: '_blank', rel: 'noopener noreferrer', className: 'text-[#b91c1c] underline hover:no-underline' }, link[1]));
      rest = rest.slice(rest.indexOf(link[0]) + link[0].length);
    } else if (bold) {
      const before = rest.slice(0, rest.indexOf(bold[0]));
      if (before) out.push(before);
      out.push(React.createElement('strong', { key: out.length }, bold[1]));
      rest = rest.slice(rest.indexOf(bold[0]) + bold[0].length);
    } else {
      out.push(rest);
      break;
    }
  }
  return out.length === 1 && typeof out[0] === 'string' ? out[0] : out;
}

export default function LegalPage({ pageKey, language, onClose }) {
  const content = getLegalContent(pageKey, language);
  if (!content) return null;

  const blocks = content.content.split(/\n\n+/).map((line, i) => renderBlock(line, i)).filter(Boolean);

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-white" aria-modal="true" role="dialog" aria-labelledby="legal-title">
      <div className="flex items-center justify-between border-b border-[#1e3a5f]/20 px-4 py-3 bg-[#1e3a5f]/5">
        <h1 id="legal-title" className="text-lg font-semibold text-[#1e3a5f]">
          {content.title}
        </h1>
        <button
          type="button"
          onClick={onClose}
          className="p-2 rounded-lg text-[#1e3a5f]/80 hover:bg-[#1e3a5f]/10 transition-colors"
          aria-label={language === 'en' ? 'Close' : 'बन्द गर्नुहोस्'}
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 max-w-3xl mx-auto w-full">
        <div className="legal-content space-y-1">{blocks}</div>
      </div>
    </div>
  );
}
