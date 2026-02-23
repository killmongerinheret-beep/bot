'use client';

export const dynamic = 'force-dynamic';

import { useUser, UserButton, SignInButton, SignUpButton } from "@clerk/nextjs";
import Link from 'next/link';
import { motion, useScroll, useTransform } from 'framer-motion';
import {
  ArrowRight,
  Zap,
  Shield,
  Eye,
  Clock,
  Bell,
  ShoppingCart,
  Link2,
  MessageCircle,
  ChevronDown,
  Globe,
  Search,
  Target,
  Server
} from 'lucide-react';
import { useState, useRef } from 'react';

export default function LandingPage() {
  const { isSignedIn, isLoaded } = useUser();
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const scrollRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: scrollRef });

  const fadeIn = {
    hidden: { opacity: 0, y: 30 },
    show: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] as const } }
  };

  const stagger = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.15 } }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-[#00E37C] selection:text-[#050505]" ref={scrollRef}>

      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-[#050505]/80 backdrop-blur-xl border-b border-[#262626]">
        <div className="container mx-auto px-8 h-24 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#00E37C] rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(0,227,124,0.3)]">
              <span className="text-xl font-black text-[#050505]">H</span>
            </div>
            <span className="text-xl font-bold tracking-tight">HYDRA</span>
          </div>

          <div className="flex items-center gap-8">
            <div className="hidden md:flex items-center gap-6 text-sm font-medium text-[#888888]">
              <Link href="#features" className="hover:text-white transition-colors">Features</Link>
              <Link href="#pricing" className="hover:text-white transition-colors">Pricing</Link>
              <Link href="#faq" className="hover:text-white transition-colors">FAQ</Link>
            </div>

            {isLoaded && isSignedIn ? (
              <div className="flex items-center gap-4">
                <Link href="/dashboard" className="btn-secondary !py-3 !px-6 hover:bg-white/10">
                  Dashboard
                </Link>
                <UserButton afterSignOutUrl="/" />
              </div>
            ) : (
              <div className="flex items-center gap-4">
                <SignInButton mode="modal">
                  <button className="text-sm font-medium text-[#888888] hover:text-white transition-colors px-4 py-2">
                    Sign In
                  </button>
                </SignInButton>
                <SignUpButton mode="modal">
                  <button className="btn-primary !py-3 !px-8 text-sm shadow-[0_0_30px_rgba(0,227,124,0.4)] hover:shadow-[0_0_50px_rgba(0,227,124,0.6)]">
                    Get Access
                  </button>
                </SignUpButton>
              </div>
            )}
          </div>
        </div>
      </nav>

      <main>
        {/* ================= HERO SECTION ================= */}
        <section className="relative pt-48 pb-32 overflow-hidden">
          <div className="container mx-auto px-8 relative z-10">
            <motion.div
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              variants={stagger}
              className="max-w-5xl mx-auto text-center"
            >
              {/* Status Badge */}
              <motion.div variants={fadeIn} className="inline-flex justify-center mb-10">
                <div className="status-pill pl-2 pr-4 py-2 bg-[#00E37C]/5 border border-[#00E37C]/20 backdrop-blur-md">
                  <span className="relative flex h-3 w-3 mr-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00E37C] opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-[#00E37C]"></span>
                  </span>
                  <span className="tracking-wide">System Online: Sniffing 24,032 slots</span>
                </div>
              </motion.div>

              {/* Headline */}
              <motion.h1
                variants={fadeIn}
                className="text-7xl md:text-9xl font-semibold tracking-tighter leading-[0.9] mb-8 text-transparent bg-clip-text bg-gradient-to-b from-white to-white/40"
              >
                Sniff. Detect. <br />
                <span className="text-[#00E37C]">Snipe.</span>
              </motion.h1>

              {/* Subheadline */}
              <motion.p
                variants={fadeIn}
                className="text-xl md:text-2xl text-[#888888] mb-12 max-w-2xl mx-auto leading-relaxed font-light"
              >
                The ultimate automated inventory system. We detect hidden availability at
                <span className="text-white font-medium"> Vatican & Colosseum </span>
                and secure it before humanly possible.
              </motion.p>

              {/* CTA Buttons */}
              <motion.div
                variants={fadeIn}
                className="flex flex-col sm:flex-row items-center justify-center gap-6"
              >
                <SignUpButton mode="modal">
                  <button className="btn-primary !text-lg !px-10 !py-5 shadow-[0_0_40px_rgba(0,227,124,0.3)]">
                    Start Sniping
                    <ArrowRight size={20} className="ml-2 group-hover:translate-x-1 transition-transform" />
                  </button>
                </SignUpButton>
                <SignUpButton mode="modal">
                  <button className="btn-secondary !text-lg !px-10 !py-5 hover:border-white/40">
                    View Live Demo
                  </button>
                </SignUpButton>
              </motion.div>
            </motion.div>
          </div>

          {/* Background Elements */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[500px] bg-[#00E37C]/10 rounded-full blur-[120px] pointer-events-none opacity-50 mix-blend-screen" />
          <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />
        </section>


        {/* ================= BENTO GRID SECTION ================= */}
        <section id="features" className="py-32">
          <div className="container mx-auto px-8">
            <motion.div
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: "-100px" }}
              variants={stagger}
              className="grid grid-cols-1 md:grid-cols-4 gap-6 max-w-7xl mx-auto"
            >

              {/* Card 1: Main Value Prop (Large) */}
              <motion.div
                variants={fadeIn}
                className="bento-card col-span-1 md:col-span-2 row-span-2 min-h-[500px] relative group"
              >
                <div className="relative z-10 flex flex-col h-full justify-between">
                  <div>
                    <div className="w-14 h-14 bg-[#00E37C] text-[#050505] rounded-2xl flex items-center justify-center mb-8 shadow-[0_0_30px_rgba(0,227,124,0.3)]">
                      <Zap size={28} strokeWidth={2.5} />
                    </div>
                    <h3 className="text-4xl font-semibold mb-6 tracking-tight leading-tight">
                      Faster Than <br />
                      <span className="text-[#888888]">Humanly Possible.</span>
                    </h3>
                    <p className="text-[#888888] text-lg leading-relaxed max-w-md">
                      Manual refreshing is dead. Our network scans inventory every
                      <span className="text-[#00E37C] font-medium"> 0.8 seconds </span>
                      via direct API access, instantly locking tickets the moment they appear.
                    </p>
                  </div>

                  {/* Visual: Pulse Graph */}
                  <div className="mt-12 flex items-end gap-1 h-32 w-full opacity-50 group-hover:opacity-100 transition-opacity">
                    {[40, 70, 30, 85, 50, 90, 60, 40, 75, 55, 95, 30, 60].map((h, i) => (
                      <div key={i} className="flex-1 bg-[#00E37C]" style={{ height: `${h}%`, opacity: i % 2 === 0 ? 0.4 : 0.8 }}></div>
                    ))}
                  </div>
                </div>
              </motion.div>

              {/* Card 2: Proxy Tech (Tall) */}
              <motion.div
                variants={fadeIn}
                className="bento-card col-span-1 md:col-span-1 row-span-2 min-h-[500px] relative overflow-hidden group"
              >
                <div className="absolute inset-0 bg-gradient-to-b from-transparent to-[#00E37C]/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                <div className="relative z-10">
                  <div className="w-12 h-12 bg-[#262626] rounded-2xl flex items-center justify-center mb-6">
                    <Globe className="text-white" size={24} />
                  </div>
                  <h3 className="text-2xl font-semibold mb-4">Global Proxy Mesh.</h3>
                  <p className="text-[#888888] text-sm leading-relaxed mb-8">
                    Residential IP rotation ensures 99.9% uptime. We blend in with local Italian traffic.
                  </p>
                </div>

                {/* Animated Map Visual Placeholder */}
                <div className="absolute bottom-0 left-0 w-full h-1/2 opacity-30">
                  <div className="w-full h-full bg-[radial-gradient(circle_at_center,#ffffff_1px,transparent_1px)] bg-[length:20px_20px]" />
                </div>
              </motion.div>

              {/* Card 3: Deep Links (Small) */}
              <motion.div
                variants={fadeIn}
                className="bento-card col-span-1 min-h-[240px] flex flex-col justify-center"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="w-10 h-10 bg-[#262626] rounded-xl flex items-center justify-center">
                    <Target className="text-white" size={20} />
                  </div>
                  <span className="text-xs font-mono text-[#00E37C] bg-[#00E37C]/10 px-2 py-1 rounded">DETECTED</span>
                </div>
                <h3 className="text-xl font-semibold mb-2">Deep Detecting</h3>
                <p className="text-[#888888] text-sm">We find "Hidden Slots" (Tag 6) that the public calendar hides.</p>
              </motion.div>

              {/* Card 4: Stats (Small) */}
              <motion.div
                variants={fadeIn}
                className="bento-card col-span-1 min-h-[240px] flex flex-col justify-center bg-[#00E37C] !border-none"
              >
                <div className="text-[#050505]">
                  <div className="text-6xl font-black mb-2 tracking-tighter">0.8s</div>
                  <div className="font-semibold text-lg opacity-80">Scan Latency</div>
                  <div className="mt-4 text-sm font-medium opacity-60">The fastest in the market.</div>
                </div>
              </motion.div>

              {/* Card 5: Wide Bottom (Notification) */}
              <motion.div
                variants={fadeIn}
                className="bento-card col-span-1 md:col-span-2 min-h-[300px] flex flex-row items-center justify-between"
              >
                <div className="max-w-sm">
                  <div className="w-12 h-12 bg-[#262626] rounded-2xl flex items-center justify-center mb-6">
                    <Bell className="text-white" size={24} />
                  </div>
                  <h3 className="text-2xl font-semibold mb-4">Instant Alerts.</h3>
                  <p className="text-[#888888]">
                    Get notified via Telegram instantly. One tap to cart.
                  </p>
                </div>

                {/* Visual: Notification Mockup */}
                <div className="hidden md:block w-64 bg-[#1a1a1a] rounded-xl p-4 border border-[#333] shadow-2xl transform rotate-3 hover:rotate-0 transition-transform duration-500">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-8 h-8 rounded-full bg-[#00E37C] flex items-center justify-center text-[#050505] font-bold">S</div>
                    <div>
                      <div className="text-xs font-bold text-white">SniffAndSnipe</div>
                      <div className="text-[10px] text-[#888888]">now</div>
                    </div>
                  </div>
                  <div className="text-xs text-white mb-2">🎟️ <b>Vatican Available!</b></div>
                  <div className="text-[10px] text-[#888888]">2 Tickets • 19/03/2026 • 09:00 AM</div>
                  <div className="mt-3 w-full bg-[#00E37C] h-6 rounded text-[#050505] text-[10px] font-bold flex items-center justify-center">ADD TO CART</div>
                </div>
              </motion.div>

              {/* Card 6: Sniper Mode */}
              <motion.div
                variants={fadeIn}
                className="bento-card col-span-1 md:col-span-2 min-h-[300px] flex flex-col justify-center"
              >
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 bg-purple-500/20 rounded-2xl flex items-center justify-center">
                    <ShoppingCart className="text-purple-400" size={24} />
                  </div>
                  <div className="px-3 py-1 bg-purple-500/10 border border-purple-500/20 rounded-full text-xs font-bold text-purple-400">
                    SNIPER MODE
                  </div>
                </div>
                <h3 className="text-2xl font-semibold mb-4">Auto-Checkout.</h3>
                <p className="text-[#888888] max-w-lg">
                  Don't even click. Enable Sniper Mode and we'll secure the reservation automatically, sending you a <span className="text-white">Magic Link</span> to complete payment.
                </p>
              </motion.div>

            </motion.div>
          </div>
        </section>

        {/* ================= HOW IT WORKS ================= */}
        <section className="py-32 border-t border-[#1a1a1a]">
          <div className="container mx-auto px-8">
            <motion.h2
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              className="text-center text-4xl font-semibold mb-20 tracking-tight"
            >
              The Sniffing Protocol
            </motion.h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-12 relative">
              {[
                {
                  step: "01",
                  title: "Define Target",
                  desc: "Select venue, date, and pax. Upload names for auto-fill.",
                },
                {
                  step: "02",
                  title: "The Sniff",
                  desc: "Our bots swarm the API endpoints, checking every 800ms.",
                },
                {
                  step: "03",
                  title: "The Snipe",
                  desc: "We lock the cart and send you the checkout key.",
                }
              ].map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.2 }}
                  className="relative"
                >
                  <div className="text-[#262626] text-[120px] font-black absolute -top-16 -left-6 z-0 opacity-50 select-none">
                    {item.step}
                  </div>
                  <div className="relative z-10 pt-12">
                    <h3 className="text-2xl font-bold mb-4">{item.title}</h3>
                    <p className="text-[#888888] leading-relaxed max-w-xs">{item.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ================= PRICING ================= */}
        <section id="pricing" className="py-32 bg-[#0a0a0a]">
          <div className="container mx-auto px-8">
            <div className="text-center max-w-2xl mx-auto mb-20">
              <h2 className="text-4xl font-semibold mb-6">Pricing Models</h2>
              <p className="text-[#888888]">Flexible options for independent agents and large operators.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              {/* Standard */}
              <div className="bento-card p-10 flex flex-col">
                <div className="mb-8">
                  <h3 className="text-xl font-bold mb-2">The Watcher</h3>
                  <div className="text-4xl font-bold">€299 <span className="text-lg text-[#888888] font-normal">/mo</span></div>
                </div>
                <ul className="space-y-4 mb-10 flex-1">
                  <li className="flex items-center gap-3 text-[#888888]">
                    <div className="w-1.5 h-1.5 rounded-full bg-white"></div> Unlimited Monitors
                  </li>
                  <li className="flex items-center gap-3 text-[#888888]">
                    <div className="w-1.5 h-1.5 rounded-full bg-white"></div> Telegram Alerts
                  </li>
                  <li className="flex items-center gap-3 text-[#888888]">
                    <div className="w-1.5 h-1.5 rounded-full bg-white"></div> 5s Scan Interval
                  </li>
                </ul>
                <SignUpButton mode="modal">
                  <button className="btn-secondary w-full justify-center">Start Trial</button>
                </SignUpButton>
              </div>

              {/* Pro */}
              <div className="bento-card p-10 flex flex-col relative border-[#00E37C]/50 shadow-[0_0_50px_rgba(0,227,124,0.1)]">
                <div className="absolute top-0 right-0 bg-[#00E37C] text-[#050505] text-xs font-bold px-4 py-1 rounded-bl-xl">
                  BEST VALUE
                </div>
                <div className="mb-8">
                  <h3 className="text-xl font-bold mb-2 text-[#00E37C]">The Sniper</h3>
                  <div className="text-4xl font-bold">€10 <span className="text-lg text-[#888888] font-normal">/successful snipe</span></div>
                </div>
                <ul className="space-y-4 mb-10 flex-1">
                  <li className="flex items-center gap-3 text-white">
                    <Zap size={16} className="text-[#00E37C]" /> Auto-Checkout
                  </li>
                  <li className="flex items-center gap-3 text-white">
                    <Zap size={16} className="text-[#00E37C]" /> 0.8s Ultra-Fast Scan
                  </li>
                  <li className="flex items-center gap-3 text-white">
                    <Zap size={16} className="text-[#00E37C]" /> Dedicated Residential IPs
                  </li>
                  <li className="flex items-center gap-3 text-white">
                    <Zap size={16} className="text-[#00E37C]" /> No Monthly Fees
                  </li>
                </ul>
                <SignUpButton mode="modal">
                  <button className="btn-primary w-full justify-center">Request Access</button>
                </SignUpButton>
              </div>
            </div>
          </div>
        </section>

        {/* ================= FOOTER ================= */}
        <footer className="py-20 border-t border-[#262626]">
          <div className="container mx-auto px-8">
            <div className="flex flex-col md:flex-row justify-between items-center gap-8">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-[#262626] rounded-lg flex items-center justify-center text-[#00E37C] font-bold">H</div>
                <span className="font-bold text-lg">HYDRA</span>
              </div>
              <div className="text-[#888888] text-sm">
                © 2026 Hydra Monitoring. Rome, Italy.
              </div>
              <div className="flex gap-6">
                <Link href="#" className="text-[#888888] hover:text-white transition-colors">Legal</Link>
                <Link href="#" className="text-[#888888] hover:text-white transition-colors">Privacy</Link>
                <Link href="#" className="text-[#888888] hover:text-white transition-colors">Contact</Link>
              </div>
            </div>
          </div>
        </footer>

      </main>
    </div>
  );
}
