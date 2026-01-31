import React from 'react';

/**
 * Catches React render errors and shows a fallback UI instead of a blank screen.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex flex-col items-center justify-center p-4 sm:p-6 bg-gradient-to-br from-[#1e3a5f]/5 to-[#b91c1c]/5 overflow-x-hidden" role="alert">
          <div className="max-w-md w-full bg-white rounded-xl border border-[#1e3a5f]/20 shadow-lg p-4 sm:p-6 text-center mx-2 sm:mx-4">
            <h1 className="text-xl font-semibold text-[#1e3a5f] mb-2">
              Something went wrong
            </h1>
            <p className="text-sm text-[#1e3a5f]/80 mb-4">
              कृपया पृष्ठ पुनः लोड गर्नुहोस् वा पछि फेरि प्रयास गर्नुहोस्।
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="min-h-[44px] px-4 py-2.5 bg-[#b91c1c] text-white rounded-lg text-sm font-medium hover:bg-[#b91c1c]/90 transition-colors touch-manipulation"
            >
              Reload page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
