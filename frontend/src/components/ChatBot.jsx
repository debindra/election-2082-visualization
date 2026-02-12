import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { queryRAG, resetRAGSession } from '../services/api';
import PollingCentersList from './PollingCentersList';

const ChatBot = ({ language = 'ne' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);
  const [showRetry, setShowRetry] = useState(false);
  const [copiedMessageIndex, setCopiedMessageIndex] = useState(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const chatWindowRef = useRef(null);

  // Quick suggestion prompts
  const quickSuggestions = [
    { ne: 'मेरो मतदान केन्द्र कहाँ छ?', en: 'Where is my polling center?' },
    { ne: 'उम्मेदवारहरूको बारेमा जान्नुहोस्', en: 'Tell me about candidates' },
    { ne: 'निर्वाचन परिणाम', en: 'Election results' },
    { ne: 'मतदाता पहिचान पत्र', en: 'Voter ID card information' },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const generateSessionId = () => {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  };

  const handleSend = async (e) => {
    e?.preventDefault();

    if (!input.trim()) return;

    const currentSessionId = sessionId || generateSessionId();
    if (!sessionId) {
      setSessionId(currentSessionId);
    }

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);
    setShowRetry(false);

    try {
      const response = await queryRAG(input);

      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources || [],
        queryType: response.query_type,
        intent: response.intent,
        entities: response.entities,
        method: response.method,
        analyticsUsed: response.analytics_used,
        metadata: response.metadata,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (err) {
      console.error('Error sending message:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to send message');
      setShowRetry(true);
      setMessages(prev => [...prev, {
        role: 'error',
        content: language === 'ne' ? 'माफी गरिएको त्रुटि भयो। पुनः प्रयास गर्नुहोस्।' : 'An error occurred. Please try again.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const resetSession = async () => {
    if (!sessionId) return;
    
    try {
      await resetRAGSession(sessionId);
      setSessionId(null);
      setMessages([]);
      setError(null);
    } catch (err) {
      console.error('Error resetting session:', err);
      setError(language === 'ne' ? 'सेसन रिसेट गर्न सकेन।' : 'Failed to reset session.');
    }
  };

  const copyToClipboard = async (text, index) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageIndex(index);
      setTimeout(() => setCopiedMessageIndex(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatCandidatesList = (sources, lang) => {
    if (!sources || sources.length === 0) return null;
    
    return sources.map((source, idx) => {
      const name = source.candidate_full_name || source['Candidate Name'] || source.candidateName || '';
      const party = source.political_party || source.party || source['Party Name'] || '';
      const election_symbol = source.election_symbol || source['Election Symbol'] || '';
      const education = source.academic_qualification || source.education || source['Academic Qualification'] || 'N/A';
      // const age = source.dob || 'N/A';
      const currentNepaliYear = 2082;

const age = source.dob
  ? currentNepaliYear - parseInt(source.dob.split('-')[0])
  : 'N/A';

      
      return (
        <div key={idx} className="mb-4">
          <div className="font-semibold text-[#1e3a5f]">{idx + 1}. {name}</div>
          <div className="text-gray-700">{party}{election_symbol ? ` (${election_symbol})` : ''}</div>
          <div className="text-sm text-gray-600">{education} | {age} yrs</div>
        </div>
      );
    });
  };

  const formatVotingCentersList = (sources, lang) => {
    if (!sources || sources.length === 0) return null;
    
    // Group by polling center name
    const grouped = {};
    sources.forEach((source, idx) => {
      const pollingCenter = source.polling_center_name || source.center_name || 'Unknown';
      if (!grouped[pollingCenter]) {
        grouped[pollingCenter] = [];
      }
      grouped[pollingCenter].push({ ...source, originalIndex: idx });
    });
    
    return Object.entries(grouped).map(([pollingCenterName, centers], pollingCenterIdx) => (
      <div key={pollingCenterName} className="mb-6">
        <div className="font-semibold text-[#1e3a5f] mb-3">
          {pollingCenterIdx + 1}: {pollingCenterName}
        </div>
        {centers.map((center, centerIdx) => (
          <div key={centerIdx} className="ml-4 mb-3">
            <div className="text-gray-800 font-medium">
            उपकेन्द्र: {center.sub_center || 'N/A'}
            </div>
            <div className="text-sm text-gray-600 ml-8">
              {center.voter_count || center.total_voters || 'N/A'} voters
            </div>
            <div className="text-xs text-gray-500 ml-8 mt-1">
              Serial: {center.voter_from_serial || 'N/A'} - {center.voter_to_serial || 'N/A'}
            </div>
          </div>
        ))}
      </div>
    ));
  };

  const formatMessage = (content) => {
    return (
      <div className="prose prose-sm max-w-none prose-headings:text-[#1e3a5f] prose-links:text-[#1e3a5f] hover:prose-links:text-[#2c4a6e]">
        <ReactMarkdown 
          remarkPlugins={[remarkGfm]}
          components={{
            a: ({ node, ...props }) => (
              <a {...props} target="_blank" rel="noopener noreferrer" className="text-[#1e3a5f] hover:text-[#b91c1c] underline" />
            ),
            code: ({ node, inline, ...props }) => (
              inline 
                ? <code {...props} className="bg-gray-100 text-[#1e3a5f] px-1 py-0.5 rounded text-xs" />
                : <code {...props} className="block bg-gray-100 p-3 rounded-lg text-xs overflow-x-auto" />
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    );
  };

  const toggleChat = () => setIsOpen(!isOpen);
  const toggleMinimize = () => setIsMinimized(!isMinimized);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={toggleChat}
          className="group flex items-center justify-center w-14 h-14 bg-[#1e3a5f] text-white rounded-full shadow-lg hover:bg-[#2c4a6e] hover:shadow-xl transition-all duration-300 relative"
          aria-label={language === 'ne' ? 'च्याटबट खोल्नुहोस्' : 'Open Chatbot'}
        >
          <svg className="w-6 h-6 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8c0 1.574.512 3.042 1.395 4.28L21 12z" />
          </svg>
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-[#b91c1c] rounded-full animate-pulse" />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div 
          ref={chatWindowRef}
          className={`fixed bottom-4 right-4 w-full max-w-md bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden transition-all duration-300 ${
            isMinimized ? 'h-14' : 'h-[600px]'
          }`}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-[#1e3a5f] to-[#2c4a6e] text-white px-4 py-3 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <div className="relative">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8c0 1.574.512 3.042 1.395 4.28L21 12z" />
                </svg>
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-[#1e3a5f]" />
              </div>
              <div>
                <span className="font-semibold text-sm">
                  {language === 'ne' ? 'चुनाव विश्लेषण' : 'Election Assistant'}
                </span>
                <div className="text-xs text-white/70">
                  {language === 'ne' ? 'अनलाइन' : 'Online'}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={toggleMinimize}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                title={language === 'ne' ? 'घटाउनुहोस्' : 'Minimize'}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                </svg>
              </button>
              <button
                onClick={resetSession}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                title={language === 'ne' ? 'सेसन रिसेट' : 'Reset Session'}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
              <button
                onClick={toggleChat}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                aria-label={language === 'ne' ? 'बन्द गर्नुहोस्' : 'Close'}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {!isMinimized && (
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-gray-50 to-white">
                {messages.length === 0 && (
                  <div className="text-center text-gray-500 mt-8 space-y-6">
                    <div className="relative inline-block">
                      <div className="w-20 h-20 bg-gradient-to-br from-[#1e3a5f]/10 to-[#b91c1c]/10 rounded-full flex items-center justify-center mx-auto">
                        <svg className="w-10 h-10 text-[#1e3a5f]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8c0 1.574.512 3.042 1.395 4.28L21 12z" />
                        </svg>
                      </div>
                      <div className="absolute -top-1 -right-1 w-6 h-6 bg-[#b91c1c] rounded-full flex items-center justify-center animate-bounce">
                        <span className="text-white text-xs font-bold">AI</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-base font-medium text-[#1e3a5f]">
                        {language === 'ne' ? 'आज निर्वाचन प्रश्न गर्नुहोस्' : 'Ask me anything about the election'}
                      </p>
                      <p className="text-xs mt-2 text-gray-500">
                        {language === 'ne' ? 'उम्मेदवारहरू, मतदान केन्द्रहरू, आदि...' : 'Candidates, polling centers, and more...'}
                      </p>
                    </div>
                    
                    {/* Quick Suggestions */}
                    <div className="pt-4">
                      <p className="text-xs text-gray-500 mb-3">
                        {language === 'ne' ? 'द्रुत प्रश्नहरू' : 'Quick questions'}
                      </p>
                      <div className="flex flex-wrap gap-2 justify-center">
                        {quickSuggestions.map((suggestion, idx) => (
                          <button
                            key={idx}
                            onClick={() => {
                              setInput(suggestion[language]);
                              inputRef.current?.focus();
                            }}
                            className="px-3 py-2 bg-white border border-gray-200 rounded-full text-xs text-[#1e3a5f] hover:border-[#1e3a5f] hover:bg-[#1e3a5f]/5 transition-all"
                          >
                            {suggestion[language]}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} slide-up`}
                    style={{ animationDelay: `${idx * 50}ms` }}
                  >
                    <div className={`relative max-w-[85%] rounded-2xl px-4 py-3 shadow-sm ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-br from-[#1e3a5f] to-[#2c4a6e] text-white'
                        : msg.role === 'error'
                        ? 'bg-red-50 border border-red-200 text-red-800'
                        : 'bg-white border border-gray-200 text-gray-800'
                    }`}>
                      {/* Message content */}
                      {msg.role !== 'error' && (
                        <>
                          {/* Display summary first, then list */}
                          {msg.content && (
                            <div className="mb-4">
                              {formatMessage(msg.content)}
                            </div>
                          )}

                          {/* Render formatted list for candidates/voting centers */}
                          {msg.entities?.target === 'candidates' && msg?.queryType === 'EXACT_LOOKUP' && msg?.intent !== 'count' && formatCandidatesList(msg.sources, language) && (
                            <div className="space-y-2">
                              {formatCandidatesList(msg.sources, language)}
                            </div>
                          )}
                          {msg.entities?.target === 'voting_centers' && msg?.queryType === 'EXACT_LOOKUP'  && msg?.intent !== 'count' && formatVotingCentersList(msg.sources, language) && (
                            <div className="space-y-2">
                              {formatVotingCentersList(msg.sources, language)}
                            </div>
                          )}
                        </>
                      )}
                      {msg.role === 'error' && (
                        <div className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span className="text-sm">{msg.content}</span>
                        </div>
                      )}
                      
                      {/* Message actions */}
                      {msg.role === 'assistant' && (
                        <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-200">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs text-gray-500">
                              {language === 'ne' ? 'प्रश्न प्रकार' : 'Query Type'}: {msg.queryType || 'N/A'}
                            </span>
                            {msg.intent && (
                              <span className="text-xs text-[#1e3a5f] font-medium bg-[#1e3a5f]/5 px-2 py-0.5 rounded-full">
                                {language === 'ne' ? 'उद्देश्य' : 'Intent'}: {msg.intent}
                              </span>
                            )}
                            {msg.entities && Object.keys(msg.entities).length > 0 && (
                              <span className="text-xs text-gray-600">
                                {language === 'ne' ? 'सत्ताहरू' : 'Entities'}: {Object.entries(msg.entities)
                                  .filter(([_, v]) => v && v !== null && v !== 'auto')
                                  .map(([k, v]) => {
                                    // Handle array values like party names or districts
                                    if (Array.isArray(v)) {
                                      return v.slice(0, 2).join(', ') + (v.length > 2 ? ` +${v.length - 2}` : '');
                                    }
                                    // Handle other values
                                    return v;
                                  })
                                  .filter(Boolean)
                                  .join(', ')}
                              </span>
                            )}
                            {msg.method && (
                              <span className="text-xs text-gray-500">
                                • {msg.method}
                              </span>
                            )}
                          </div>
                          <button
                            onClick={() => copyToClipboard(msg.content, idx)}
                            className="flex items-center gap-1 text-xs text-gray-500 hover:text-[#1e3a5f] transition-colors"
                            title={language === 'ne' ? 'प्रतिलिपि बनाउनुहोस्' : 'Copy'}
                          >
                            {copiedMessageIndex === idx ? (
                              <>
                                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                <span>{language === 'ne' ? 'प्रतिलिपि' : 'Copied'}</span>
                              </>
                            ) : (
                              <>
                                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                              </>
                            )}
                          </button>
                        </div>
                      )}
                      
                      {/* Timestamp */}
                      {msg.timestamp && (
                        <div className={`text-[10px] mt-1 ${msg.role === 'user' ? 'text-white/60' : 'text-gray-400'}`}>
                          {formatTime(msg.timestamp)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {/* Typing indicator */}
                {loading && (
                  <div className="flex justify-start slide-up">
                    <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                      <div className="flex items-center gap-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-[#1e3a5f] rounded-full animate-bounce" />
                          <div className="w-2 h-2 bg-[#1e3a5f] rounded-full animate-bounce delay-100" />
                          <div className="w-2 h-2 bg-[#1e3a5f] rounded-full animate-bounce delay-200" />
                        </div>
                        <span className="text-xs text-gray-500">
                          {language === 'ne' ? 'लेख्दैछ...' : 'Typing...'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <form onSubmit={handleSend} className="border-t border-gray-200 bg-white p-4 shrink-0">
                {error && (
                  <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-xl text-red-800 text-sm flex items-start gap-2">
                    <svg className="w-5 h-5 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div className="flex-1">
                      <p>{error}</p>
                      {showRetry && (
                        <button
                          type="button"
                          onClick={handleSend}
                          className="mt-2 text-sm font-medium text-red-700 hover:text-red-900 underline"
                        >
                          {language === 'ne' ? 'पुनः प्रयास गर्नुहोस्' : 'Try again'}
                        </button>
                      )}
                    </div>
                  </div>
                )}

                <div className="flex gap-2">
                  {/* Text Input */}
                  <div className="flex-1 relative">
                    <input
                      ref={inputRef}
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder={
                        language === 'ne' 
                          ? 'आफ्नो प्रश्न गर्नुहोस्...' 
                          : 'Ask your question...'
                      }
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e3a5f]/30 focus:border-[#1e3a5f] transition-all text-sm"
                      disabled={loading}
                      maxLength={500}
                    />
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-gray-400">
                      {input.length}/500
                    </div>
                  </div>

                  {/* Send Button */}
                  <button
                    type="submit"
                    disabled={loading || !input.trim()}
                    className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-[#1e3a5f] to-[#2c4a6e] text-white rounded-xl hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all disabled:hover:shadow-none flex items-center justify-center"
                    aria-label={language === 'ne' ? 'पठाउनुहोस्' : 'Send'}
                  >
                    {loading ? (
                      <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                      </svg>
                    )}
                  </button>
                </div>

                {/* Keyboard hint */}
                <div className="mt-2 text-[10px] text-gray-400 text-center">
                  {language === 'ne' ? 'Enter थिच्नुहोस् पठाउन, Shift+Enter नया लाइन' : 'Press Enter to send, Shift+Enter for new line'}
                </div>
              </form>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default ChatBot;
