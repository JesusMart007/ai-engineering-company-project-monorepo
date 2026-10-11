import React from 'react';
import Link from 'next/link';
import { SUPPORT_EMAIL } from '../utils/errors';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
  title?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  message,
  onRetry,
  title = 'Ha ocurrido un error',
}) => {
  return (
    <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-6 my-4 dark:border-red-900/50 dark:bg-red-950/40 text-red-900 dark:text-red-200">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 text-red-600 dark:text-red-400 mt-0.5">
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-base font-semibold text-red-900 dark:text-red-100">
            {title}
          </h3>
          <p className="mt-1 text-sm text-red-800 dark:text-red-200">{message}</p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            {onRetry && (
              <button
                onClick={onRetry}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium text-sm rounded-lg transition-colors shadow-sm cursor-pointer"
              >
                Reintentar
              </button>
            )}
            <Link
              href="/"
              className="px-4 py-2 border border-red-300 dark:border-red-800 hover:bg-red-100 dark:hover:bg-red-900/40 font-medium text-sm rounded-lg transition-colors"
            >
              Volver al inicio
            </Link>
          </div>
          <p className="mt-3 text-xs text-red-700 dark:text-red-300">
            Si el problema continúa, escríbenos a{' '}
            <a href={`mailto:${SUPPORT_EMAIL}`} className="underline">
              {SUPPORT_EMAIL}
            </a>
            .
          </p>
        </div>
      </div>
    </div>
  );
};

export default ErrorState;
