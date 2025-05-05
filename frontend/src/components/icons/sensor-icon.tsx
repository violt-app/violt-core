export function SensorIcon({ className }: { readonly className?: string }) {
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
            <path d="M7 22H2V7h10" />
            <path d="M22 7v10.5c0 .83-.67 1.5-1.5 1.5s-1.5-.67-1.5-1.5V10h-8V7h11Z" />
            <path d="M7 7v10.5c0 .83-.67 1.5-1.5 1.5S4 18.33 4 17.5V7" />
            <path d="M4 7V5c0-1.1.9-2 2-2h12a2 2 0 0 1 2 2v2" />
            <path d="M11 16a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" />
        </svg>
    );
}