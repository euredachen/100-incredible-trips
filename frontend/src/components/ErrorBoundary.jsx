import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6"
             style={{ backgroundColor: 'var(--color-surface)' }}>
          <div className="glass-card p-8 max-w-md text-center">
            <p style={{ fontSize: '40px' }}>😵</p>
            <h2 className="text-lg font-semibold mt-4 mb-2"
                style={{ color: 'var(--color-text)' }}>
              页面出了点问题
            </h2>
            <p className="text-sm mb-6"
               style={{ color: 'var(--color-text-secondary)' }}>
              {this.state.error?.message || '未知错误'}
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
              className="px-6 py-2.5 rounded-full text-white font-medium"
              style={{ backgroundColor: 'var(--accent-warm)' }}
            >
              重新加载
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
