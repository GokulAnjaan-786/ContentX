import React from "react";
import { AlertCircle, XCircle } from "lucide-react";

export interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = "An error occurred",
  message,
  onRetry,
  className = "",
}) => {
  if (!message) return null;

  return (
    <div
      role="alert"
      className={`rounded-xl border border-red-200 bg-red-50 p-4 text-red-900 ${className}`}
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
        <div className="flex-1 text-sm">
          <p className="font-semibold text-red-800">{title}</p>
          <p className="mt-1 text-red-700 leading-relaxed">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center text-xs font-semibold text-red-700 underline hover:text-red-900"
            >
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
