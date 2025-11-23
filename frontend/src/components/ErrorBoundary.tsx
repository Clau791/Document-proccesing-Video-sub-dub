import React from "react";

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean; error?: any }> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: undefined };
  }

  static getDerivedStateFromError(error: any) {
    return { hasError: true, error };
  }

  componentDidCatch(error: any, info: any) {
    console.error("UI crashed:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen grid place-items-center bg-gradient-to-br from-white via-sky-50 to-blue-50 p-6">
          <div className="max-w-lg w-full bg-white/90 backdrop-blur border border-gray-200 rounded-2xl p-6 shadow-xl">
            <h2 className="text-xl font-bold mb-2 text-gray-800">A apărut o eroare în UI</h2>
            <p className="text-sm text-gray-600 mb-4">Verifică dependențele și componentele recente.</p>
            <pre className="text-xs text-red-600 whitespace-pre-wrap bg-red-50 border border-red-200 rounded-lg p-3 overflow-auto max-h-48">
              {String(this.state.error)}
            </pre>
            <button
              className="mt-4 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-sky-500 text-white"
              onClick={() => location.reload()}
            >
              Reîncarcă
            </button>
          </div>
        </div>
      );
    }
    return this.props.children as any;
  }
}

export default ErrorBoundary;
