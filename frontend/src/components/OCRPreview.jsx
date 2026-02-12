/**
 * OCR Preview Component
 * Displays OCR extracted text and confidence from voter card
 */
import React, { useState } from 'react';

const OCRPreview = ({ ocrText, ocrConfidence, voterCardEntities, language = 'ne' }) => {
  const [expanded, setExpanded] = useState(false);

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return 'text-green-600 bg-green-50 border-green-200';
    if (confidence >= 60) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 80) return language === 'ne' ? 'उत्तम' : 'High';
    if (confidence >= 60) return language === 'ne' ? 'मध्यम' : 'Medium';
    return language === 'ne' ? 'निम्न' : 'Low';
  };

  const getConfidenceIcon = (confidence) => {
    if (confidence >= 80) return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    );
    if (confidence >= 60) return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    );
    return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    );
  };

  if (!ocrText) return null;

  const displayText = expanded ? ocrText : ocrText.slice(0, 200) + (ocrText.length > 200 ? '...' : '');

  return (
    <div className="mb-4 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-white/50 border-b border-blue-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-sm font-semibold text-blue-800">
            {language === 'ne' ? 'OCR बाट निकाला:' : 'OCR Extracted Text:'}
          </h3>
        </div>
        
        {/* Confidence Badge */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${getConfidenceColor(ocrConfidence)}`}>
          {getConfidenceIcon(ocrConfidence)}
          <span>{getConfidenceLabel(ocrConfidence)}</span>
          <span className="font-normal opacity-75">({ocrConfidence?.toFixed(1) || 'N/A'}%)</span>
        </div>
      </div>

      {/* Extracted text */}
      <div className="px-4 py-3">
        <div className="bg-white rounded-lg p-3 shadow-sm">
          <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed">
            {displayText}
          </pre>
          {ocrText.length > 200 && (
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="mt-2 text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
            >
              {expanded ? (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                  </svg>
                  {language === 'ne' ? 'लुकाउनुहोस्' : 'Show less'}
                </>
              ) : (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                  {language === 'ne' ? 'थप देखाउनुहोस्' : 'Show more'}
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Extracted entities */}
      {voterCardEntities && Object.keys(voterCardEntities).length > 0 && (
        <div className="px-4 pb-3">
          <h4 className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            {language === 'ne' ? 'निकाला गएंटिटीज:' : 'Extracted Entities:'}
          </h4>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(voterCardEntities).map(([key, value]) => (
              <div 
                key={key} 
                className="bg-white rounded-lg p-2.5 shadow-sm border border-gray-100 hover:border-blue-200 transition-colors"
              >
                <div className="text-[10px] text-gray-500 uppercase tracking-wide mb-0.5">
                  {key}
                </div>
                <div className="text-xs font-semibold text-gray-800 break-words">
                  {value || language === 'ne' ? 'उपलब्ध छैन' : 'N/A'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default OCRPreview;
