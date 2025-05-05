import React from "react";
import Link from "next/link";
import Image from "next/image";
import "./landing.css";
import Logo from "@/assets/logos/violt.png"

export default function LandingPage() {
    return (
        <div className="landing-container">
            <header className="landing-header">
                <a href="https://violt.ai" target="_blank" rel="noopener noreferrer" className="logo-link">
                    <Image
                        src={Logo}
                        alt="Violt Logo"
                        priority={true}
                        placeholder="empty"
                    />
                </a>
                <h1>Welcome to Violt</h1>
                <p>Your gateway to smart automation and creativity!</p>
            </header>
            <main className="landing-main">
                <div className="landing-links">
                    <Link href="/login" className="landing-button primary">Login</Link>
                    <Link href="/register" className="landing-button secondary">Register</Link>
                </div>
                <div className="external-links">
                    <a href="https://violt.app" target="_blank" rel="noopener noreferrer">Violt App</a> | {" "}
                    <a href="https://violt.ai" target="_blank" rel="noopener noreferrer">Violt AI</a> | {" "}
                    <a href="https://github.com/violt-app" target="_blank" rel="noopener noreferrer">GitHub</a> | {" "}
                    <a href="https://github.com/violt-app/violt-core/discussions" target="_blank" rel="noopener noreferrer">Community</a>
                </div>
            </main>
        </div>
    );
}