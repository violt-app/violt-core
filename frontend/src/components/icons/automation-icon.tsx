export function AutomationIcon({ className }: { readonly className?: string }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
        >
            <path d="M12 2H2v10h10V2Z" />
            <path d="M22 12h-4v4h4v-4Z" />
            <path d="M6 16H2v6h4v-6Z" />
            <path d="M22 20h-4v4h4v-4Z" />
            <path d="M14 2h8v6h-8V2Z" />
            <path d="M6 12V8" />
            <path d="M12 12v4" />
            <path d="M16 12V8" />
        </svg>
    );
}