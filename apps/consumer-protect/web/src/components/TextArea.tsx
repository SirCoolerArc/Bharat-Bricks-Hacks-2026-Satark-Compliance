import { TextareaHTMLAttributes } from "react";

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  helperText?: string;
  error?: string;
}

export default function TextArea({ label, helperText, error, className = "", id, ...props }: TextAreaProps) {
  const textareaId = id || label?.toLowerCase().replace(/\s+/g, "-");

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={textareaId} className="text-sm font-medium text-ink">
          {label}
        </label>
      )}
      <textarea
        id={textareaId}
        className={`
          w-full px-3 py-2 rounded-md text-sm bg-white text-ink
          placeholder:text-ink-faint resize-y min-h-[80px]
          focus:outline-none focus:ring-2 focus:ring-accent/30
          transition-shadow
          ${error ? "ring-2 ring-risk-high/30" : ""}
          ${className}
        `}
        style={{ border: "0.5px solid var(--border-color)" }}
        {...props}
      />
      {helperText && !error && (
        <span className="text-xs text-ink-faint">{helperText}</span>
      )}
      {error && (
        <span className="text-xs text-risk-high">{error}</span>
      )}
    </div>
  );
}
