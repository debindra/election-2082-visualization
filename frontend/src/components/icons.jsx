import React from 'react';

// Base outline SVG icon components for reuse across the app

const baseSize = 'w-5 h-5';

export const IconSearch = ({ className = baseSize }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle
      cx="11"
      cy="11"
      r="6"
      stroke="currentColor"
      strokeWidth="1.8"
    />
    <line
      x1="16"
      y1="16"
      x2="21"
      y2="21"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
  </svg>
);

export const IconMapPin = ({ className = baseSize }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M12 21C12 21 6 14.9706 6 10C6 6.68629 8.68629 4 12 4C15.3137 4 18 6.68629 18 10C18 14.9706 12 21 12 21Z"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <circle
      cx="12"
      cy="10"
      r="2.5"
      stroke="currentColor"
      strokeWidth="1.6"
    />
  </svg>
);

export const IconBuildingColumns = ({ className = baseSize }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M4 9H20L12 4L4 9Z"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinejoin="round"
    />
    <path
      d="M6 9V17M10 9V17M14 9V17M18 9V17"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
    />
    <path
      d="M4 17H20"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
    <path
      d="M3 20H21"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
  </svg>
);

export const IconChartBar = ({ className = baseSize }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M5 20V11"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
    <path
      d="M10 20V7"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
    <path
      d="M15 20V4"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
    <path
      d="M20 20V13"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
    <path
      d="M4 20H21"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
  </svg>
);

export const IconUsers = ({ className = baseSize }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle
      cx="9"
      cy="9"
      r="3"
      stroke="currentColor"
      strokeWidth="1.8"
    />
    <path
      d="M4 18C4 15.7909 5.79086 14 8 14H10C12.2091 14 14 15.7909 14 18"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
    <circle
      cx="17"
      cy="9"
      r="2.5"
      stroke="currentColor"
      strokeWidth="1.6"
    />
    <path
      d="M15.5 14H16C18.2091 14 20 15.7909 20 18"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
    />
  </svg>
);

export const IconBallot = ({ className = baseSize }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <rect
      x="4"
      y="8"
      width="16"
      height="12"
      rx="2"
      stroke="currentColor"
      strokeWidth="1.8"
    />
    <path
      d="M9 4H15L17 8H7L9 4Z"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinejoin="round"
    />
    <path
      d="M9 12H15"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
    />
    <path
      d="M9 15H13"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
    />
  </svg>
);

export const IconClose = ({ className = baseSize }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <line
      x1="6"
      y1="6"
      x2="18"
      y2="18"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
    <line
      x1="18"
      y1="6"
      x2="6"
      y2="18"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
  </svg>
);

export const IconFlag = ({ className = baseSize }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M6 4V20"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
    <path
      d="M7 4H18L15 8L18 12H7V4Z"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinejoin="round"
    />
  </svg>
);

export const IconTable = ({ className = baseSize }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <rect x="4" y="4" width="16" height="16" rx="1.5" stroke="currentColor" strokeWidth="1.8" />
    <line x1="4" y1="10" x2="20" y2="10" stroke="currentColor" strokeWidth="1.6" />
    <line x1="4" y1="16" x2="20" y2="16" stroke="currentColor" strokeWidth="1.6" />
    <line x1="12" y1="4" x2="12" y2="20" stroke="currentColor" strokeWidth="1.6" />
  </svg>
);

// Election symbols & party logos: image paths (public/symbols/)
const SYMBOL_IMAGES = {
  सुर्य: '/symbols/CPN-UML.png',
  सूर्य: '/symbols/CPN-UML.png',
  घण्टी: '/symbols/ghanti.png',
  हलो: '/symbols/RPP-2.png',
  रुख: '/symbols/Nepali-Congress.png',
  'पाँचकुने तारा': '/symbols/Nepali-Communist-Party-removebg-preview.png',
  'मंगोल नेशनल अर्गनाइजेसन': '/symbols/Vale-1.png',
};

export function getElectionSymbolImage(symbolName) {
  if (!symbolName || typeof symbolName !== 'string') return null;
  return SYMBOL_IMAGES[symbolName.trim()] || null;
}

// Party name → same logo image as their election symbol
const PARTY_IMAGES = {
  'नेपाल कम्युनिष्ट पार्टी (एकीकृत मार्क्सवादी लेनिनवादी)': '/symbols/CPN-UML.png',
  'Communist Party of Nepal (Unified Marxist-Leninist)': '/symbols/CPN-UML.png',
  'नेपाली कम्युनिष्ट पार्टी': '/symbols/Nepali-Communist-Party-removebg-preview.png',
  'Nepali Communist Party': '/symbols/Nepali-Communist-Party-removebg-preview.png',
  'नेपाली काँग्रेस': '/symbols/Nepali-Congress.png',
  'Nepali Congress': '/symbols/Nepali-Congress.png',
  'राष्ट्रिय स्वतन्त्र पार्टी': '/symbols/ghanti.png',
  'Rastriya Swatantra Party': '/symbols/ghanti.png',
  'Rastriya Swatantra Party (RSP)': '/symbols/ghanti.png',
  'National Independence Party': '/symbols/ghanti.png',
  'RSP': '/symbols/ghanti.png',
  'rasapa': '/symbols/ghanti.png',
  'रासापा': '/symbols/ghanti.png',
  'रा सा पा': '/symbols/ghanti.png',
  'ra sa pa': '/symbols/ghanti.png',
  'राष्ट्रिय प्रजातन्त्र पार्टी': '/symbols/RPP-2.png',
  'National Democratic Party': '/symbols/RPP-2.png',
  स्वतन्त्र: '/symbols/Swatantra.png',
  Independent: '/symbols/Swatantra.png',
  'मंगोल नेशनल अर्गनाइजेसन': '/symbols/Vale-1.png',
  'Mangol National Argnayeeshan': '/symbols/Vale-1.png',
};

export function getPartyImage(partyName) {
  if (!partyName || typeof partyName !== 'string') return null;
  return PARTY_IMAGES[partyName.trim()] || null;
}

// Render election symbol or party logo as <img> (no SVG)
export function ElectionSymbolImage({ symbolName, className = 'w-8 h-8 object-contain shrink-0' }) {
  const src = getElectionSymbolImage(symbolName);
  if (!src) return null;
  return <img src={src} alt="" className={className} aria-hidden />;
}

export function PartyImage({ partyName, className = 'w-8 h-8 object-contain shrink-0' }) {
  const src = getPartyImage(partyName);
  if (!src) return null;
  return <img src={src} alt="" className={className} aria-hidden />;
}

