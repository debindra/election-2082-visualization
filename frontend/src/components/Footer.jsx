import React from 'react';

/**
 * Site footer: short disclaimer and links to Disclaimer, Privacy, Terms, Data sources.
 * Links use hash (#disclaimer, etc.) so App can show LegalPage panel.
 */
export default function Footer({ language, onLegalLinkClick }) {
  const isNe = language === 'ne';

  const disclaimerShort = isNe
    ? 'यो सूचनात्मक उद्देश्यको लागि हो। आधिकारिक नतिजा निर्वाचन आयोगको वेबसाइटमा हेर्नुहोस्।'
    : 'For informational purposes only. See Election Commission for official results.';

  const links = [
    { hash: '#disclaimer', en: 'Disclaimer', ne: 'अस्वीकरण' },
    { hash: '#privacy', en: 'Privacy', ne: 'गोपनीयता' },
    { hash: '#terms', en: 'Terms', ne: 'सर्तहरू' },
    { hash: '#data-sources', en: 'Data sources', ne: 'डाटा स्रोत' },
  ];

  return (
    <footer className="border-t border-[#1e3a5f]/20 bg-white/95 px-4 py-3 text-center text-xs text-[#1e3a5f]/80" role="contentinfo">
      <p className="mb-2 max-w-2xl mx-auto">
        {disclaimerShort}
        {' '}
        <a
          href="https://election.gov.np/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-[#b91c1c] underline hover:no-underline"
        >
          election.gov.np
        </a>
      </p>
      <p className="mb-2">
        <a
          href="mailto:deb.katwal+electionviz@gmail.com"
          className="text-[#1e3a5f]/80 hover:text-[#b91c1c] underline hover:no-underline"
        >
          {isNe ? 'सम्पर्क' : 'Contact'}: deb.katwal+electionviz@gmail.com
        </a>
      </p>
      <nav className="flex flex-wrap justify-center gap-x-4 gap-y-1" aria-label={isNe ? 'कानूनी र नीति लिंक' : 'Legal & policy links'}>
        {links.map(({ hash, en, ne }) => (
          <a
            key={hash}
            href={hash}
            onClick={(e) => {
              e.preventDefault();
              onLegalLinkClick?.(hash.slice(1));
              window.location.hash = hash;
            }}
            className="text-[#1e3a5f]/80 hover:text-[#b91c1c] underline hover:no-underline"
          >
            {isNe ? ne : en}
          </a>
        ))}
      </nav>
    </footer>
  );
}
