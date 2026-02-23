'use client';
import { useUser, UserButton, SignInButton, SignUpButton } from "@clerk/nextjs";
import Link from 'next/link';

export default function LandingPage() {
  const { isSignedIn, isLoaded } = useUser();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-md rounded-[2.5rem] p-10 shadow-xl border border-gray-100 text-center">
        <div className="mb-10">
          <div className="w-16 h-16 bg-blue-600 rounded-2xl mx-auto flex items-center justify-center text-3xl mb-6 shadow-lg shadow-blue-200">
            🌍
          </div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight mb-2">Travel Agent SaaS</h1>
          <p className="text-gray-500 text-sm font-medium">Enterprise Monument Surveillance</p>
        </div>

        {isLoaded && isSignedIn ? (
          <div className="space-y-4">
            <div className="bg-emerald-50 text-emerald-600 px-4 py-3 rounded-xl font-bold text-sm mb-6">
              ✅ You are signed in
            </div>
            <Link
              href="/dashboard"
              className="block w-full bg-blue-600 hover:bg-blue-700 text-white font-black py-4 rounded-xl transition-all shadow-lg shadow-blue-200"
            >
              Go to Dashboard &rarr;
            </Link>
            <div className="pt-4 flex justify-center">
              <UserButton afterSignOutUrl="/" />
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="bg-blue-50 text-blue-800 px-6 py-4 rounded-xl text-sm mb-6 leading-relaxed">
              Log in to access your private monitoring dashboard.
            </div>

            <SignInButton mode="modal">
              <button className="w-full bg-gray-900 hover:bg-gray-800 text-white font-black py-4 rounded-xl transition-all shadow-xl shadow-gray-200">
                Sign In
              </button>
            </SignInButton>

            <SignUpButton mode="modal">
              <button className="w-full bg-white hover:bg-gray-50 text-gray-900 border-2 border-gray-100 font-bold py-4 rounded-xl transition-all">
                Create Account
              </button>
            </SignUpButton>
          </div>
        )}
      </div>
    </div>
  );
}
