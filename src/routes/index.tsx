import { createFileRoute } from "@tanstack/react-router";
import heroBg from "@/assets/hero-bg.jpg";
import {
  MapPin, Sparkles, Globe, ShieldCheck, Rocket, Languages,
  Bot, LineChart, Lock, ArrowRight, Check, Star, Zap,
} from "lucide-react";

const BACKEND_URL =
  (import.meta.env.VITE_BACKEND_URL as string | undefined) ?? "http://localhost:8002";

const scrollTo = (id: string) => (e: React.MouseEvent) => {
  e.preventDefault();
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
};
const openBackend = (path = "/") => () => window.open(BACKEND_URL + path, "_blank", "noopener");

export const Route = createFileRoute("/")({
  component: Landing,
  head: () => ({
    meta: [
      { title: "LocalLift — Automatische Webseiten für lokale Unternehmen" },
      { name: "description", content: "Wir finden lokale Unternehmen ohne Website auf Google Maps und erstellen automatisch moderne, SEO-optimierte Landingpages mit KI." },
    ],
  }),
});

function Landing() {
  return (
    <div id="top" className="min-h-screen bg-background text-foreground overflow-x-hidden">
      <Nav />
      <Hero />
      <LogosStrip />
      <HowItWorks />
      <Features />
      <Multilingual />
      <Pricing />
      <CTA />
      <Footer />
    </div>
  );
}

function Nav() {
  return (
    <header className="fixed top-0 inset-x-0 z-50 backdrop-blur-xl bg-background/60 border-b border-border">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <a href="#top" onClick={scrollTo("top")} className="flex items-center gap-2 font-display font-bold text-lg">
          <span className="size-7 rounded-lg bg-gradient-primary shadow-glow grid place-items-center">
            <MapPin className="size-4 text-primary-foreground" />
          </span>
          LocalLift
        </a>
        <nav className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
          <a href="#how" onClick={scrollTo("how")} className="hover:text-foreground transition">So funktioniert's</a>
          <a href="#features" onClick={scrollTo("features")} className="hover:text-foreground transition">Features</a>
          <a href="#pricing" onClick={scrollTo("pricing")} className="hover:text-foreground transition">Preise</a>
          <a href="#languages" onClick={scrollTo("languages")} className="hover:text-foreground transition">Sprachen</a>
        </nav>
        <div className="flex items-center gap-3">
          <button onClick={openBackend("/")} className="text-sm text-muted-foreground hover:text-foreground transition hidden sm:block">Login</button>
          <button onClick={openBackend("/")} className="bg-gradient-primary text-primary-foreground px-4 py-2 rounded-lg text-sm font-medium shadow-glow hover:scale-105 transition">
            Admin öffnen
          </button>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="relative pt-40 pb-32 px-6">
      <img
        src={heroBg}
        alt=""
        width={1920}
        height={1280}
        className="absolute inset-0 w-full h-full object-cover opacity-40 -z-10"
      />
      <div className="absolute inset-0 grid-bg -z-10" />
      <div className="absolute inset-x-0 top-0 h-[600px] -z-10" style={{ background: "var(--gradient-hero)" }} />

      <div className="max-w-5xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-border bg-card/40 backdrop-blur text-xs text-muted-foreground mb-8">
          <span className="size-1.5 rounded-full bg-accent animate-pulse-glow" />
          Vollautomatisch · KI-generiert · DSGVO-konform
        </div>
        <h1 className="text-5xl md:text-7xl font-bold leading-[1.05] tracking-tight">
          Webseiten für Unternehmen,<br />
          <span className="text-gradient">die noch keine haben.</span>
        </h1>
        <p className="mt-7 text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">
          Wir scannen Google Maps, finden lokale Unternehmen ohne Online-Auftritt und
          erstellen automatisch moderne, SEO-optimierte Landingpages — bereit zum Claimen.
        </p>
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button onClick={openBackend("/")} className="group bg-gradient-primary text-primary-foreground px-6 py-3 rounded-xl font-medium shadow-glow hover:scale-105 transition flex items-center gap-2">
            Jetzt starten <ArrowRight className="size-4 group-hover:translate-x-1 transition" />
          </button>
          <button onClick={openBackend("/sites")} className="px-6 py-3 rounded-xl font-medium border border-border bg-card/40 backdrop-blur hover:bg-card transition">
            Beispielseite ansehen
          </button>
        </div>

        <div className="mt-20 relative">
          <div className="absolute inset-0 bg-gradient-primary opacity-20 blur-3xl rounded-full" />
          <DashboardMock />
        </div>
      </div>
    </section>
  );
}

function DashboardMock() {
  const sites = [
    { name: "Friseur Müller", city: "Berlin", status: "Live", color: "bg-accent" },
    { name: "Pizzeria Roma", city: "München", status: "Generiert", color: "bg-primary" },
    { name: "Auto Schmidt", city: "Hamburg", status: "Claim offen", color: "bg-muted-foreground" },
    { name: "Dr. Weber Praxis", city: "Köln", status: "Live", color: "bg-accent" },
  ];
  return (
    <div className="relative mx-auto max-w-4xl rounded-2xl border border-border bg-card/80 backdrop-blur-xl shadow-elegant p-6 text-left animate-float">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <div className="size-3 rounded-full bg-destructive/60" />
          <div className="size-3 rounded-full bg-accent/60" />
          <div className="size-3 rounded-full bg-primary/60" />
        </div>
        <div className="text-xs text-muted-foreground">app.locallift.io</div>
        <div className="text-xs px-2 py-1 rounded-md bg-secondary text-muted-foreground">128 Sites</div>
      </div>
      <div className="grid sm:grid-cols-2 gap-3">
        {sites.map((s) => (
          <div key={s.name} className="flex items-center justify-between p-4 rounded-xl bg-secondary/50 border border-border hover:border-primary/40 transition">
            <div>
              <div className="font-medium text-sm">{s.name}</div>
              <div className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                <MapPin className="size-3" />{s.city}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`size-2 rounded-full ${s.color}`} />
              <span className="text-xs text-muted-foreground">{s.status}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LogosStrip() {
  const items = ["Friseure", "Restaurants", "Handwerker", "Zahnärzte", "Werkstätten", "Cafés", "Boutiquen"];
  return (
    <section className="py-16 px-6 border-y border-border">
      <p className="text-center text-xs uppercase tracking-widest text-muted-foreground mb-8">
        Funktioniert für jede lokale Branche
      </p>
      <div className="max-w-5xl mx-auto flex flex-wrap justify-center gap-x-12 gap-y-4">
        {items.map((i) => (
          <span key={i} className="font-display text-xl text-muted-foreground/60 hover:text-foreground transition">{i}</span>
        ))}
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    { icon: MapPin, title: "Scannen", text: "Google Maps Scraper findet lokale Unternehmen ohne eigene Website in jeder Stadt." },
    { icon: Sparkles, title: "Generieren", text: "KI erstellt moderne Landingpage mit Hero, Leistungen, Bewertungen & Kontaktformular." },
    { icon: ShieldCheck, title: "Claimen", text: "Geschäftsinhaber meldet sich mit Google an und übernimmt die Seite in unter einer Minute." },
  ];
  return (
    <section id="how" className="py-32 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-20">
          <div className="text-sm text-accent uppercase tracking-widest mb-3">So funktioniert's</div>
          <h2 className="text-4xl md:text-5xl font-bold">Drei Schritte, voll automatisch.</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {steps.map((s, i) => (
            <div key={s.title} className="relative p-8 rounded-2xl border border-border bg-card/40 backdrop-blur hover:border-primary/40 transition group">
              <div className="absolute -top-3 -left-3 size-10 rounded-xl bg-gradient-primary grid place-items-center shadow-glow text-primary-foreground font-bold">
                {i + 1}
              </div>
              <s.icon className="size-8 text-accent mb-5" />
              <h3 className="text-xl font-semibold mb-2">{s.title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">{s.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Features() {
  const features = [
    { icon: Bot, title: "KI-Content", text: "Hero, About, Leistungen & SEO-Texte automatisch generiert." },
    { icon: Globe, title: "Eigene Subdomain", text: "Jede Seite läuft auf firma.locallift.io oder Custom Domain." },
    { icon: Lock, title: "Lead Lock", text: "Eingehende Anfragen werden bis zum Claim sicher gespeichert." },
    { icon: LineChart, title: "Admin Dashboard", text: "Alle Sites, Claims, Leads & Conversions auf einen Blick." },
    { icon: Zap, title: "Blitzschnell", text: "Statische Generierung, Edge-Deployment, < 1s Ladezeit." },
    { icon: Rocket, title: "Auto SEO", text: "Schema.org, hreflang, Sitemaps & Meta-Tags automatisch." },
  ];
  return (
    <section id="features" className="py-32 px-6 bg-card/20 border-y border-border">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-20">
          <div className="text-sm text-accent uppercase tracking-widest mb-3">Features</div>
          <h2 className="text-4xl md:text-5xl font-bold">Alles, was eine lokale Seite braucht.</h2>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f) => (
            <div key={f.title} className="p-6 rounded-2xl border border-border bg-background/40 hover:bg-card transition group">
              <div className="size-11 rounded-xl bg-secondary grid place-items-center mb-4 group-hover:bg-gradient-primary transition">
                <f.icon className="size-5 text-accent group-hover:text-primary-foreground transition" />
              </div>
              <h3 className="font-semibold mb-1">{f.title}</h3>
              <p className="text-sm text-muted-foreground">{f.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Multilingual() {
  const langs = [
    { flag: "🇩🇪", name: "Deutsch", url: "/de/" },
    { flag: "🇬🇧", name: "English", url: "/en/" },
    { flag: "🇮🇩", name: "Indonesia", url: "/id/" },
  ];
  return (
    <section id="languages" className="py-32 px-6">
      <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-12 items-center">
        <div>
          <Languages className="size-10 text-accent mb-5" />
          <h2 className="text-4xl md:text-5xl font-bold mb-5">Drei Sprachen.<br />Ein System.</h2>
          <p className="text-muted-foreground text-lg">
            Automatische Spracherkennung, lokalisierte SEO, kulturell angepasste KI-Texte.
            Erweiterbar für jeden weiteren Markt.
          </p>
        </div>
        <div className="space-y-3">
          {langs.map((l) => (
            <div key={l.name} className="flex items-center justify-between p-5 rounded-xl border border-border bg-card/40 backdrop-blur hover:border-primary/40 transition">
              <div className="flex items-center gap-4">
                <span className="text-3xl">{l.flag}</span>
                <div>
                  <div className="font-medium">{l.name}</div>
                  <code className="text-xs text-muted-foreground">{l.url}</code>
                </div>
              </div>
              <Check className="size-5 text-accent" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Pricing() {
  return (
    <section id="pricing" className="py-32 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <div className="text-sm text-accent uppercase tracking-widest mb-3">Preise</div>
          <h2 className="text-4xl md:text-5xl font-bold">Fair. Einfach. Direkt.</h2>
        </div>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="p-8 rounded-2xl border border-border bg-card/40">
            <div className="text-sm text-muted-foreground mb-2">Free</div>
            <div className="text-5xl font-bold mb-1">0€</div>
            <div className="text-sm text-muted-foreground mb-6">für immer</div>
            <ul className="space-y-3 text-sm mb-8">
              {["Vollständige Webseite", "Lead-Formular", "Subdomain", "Mit Powered-by Badge"].map(x => (
                <li key={x} className="flex gap-2"><Check className="size-4 text-accent shrink-0 mt-0.5" />{x}</li>
              ))}
            </ul>
            <button onClick={openBackend("/")} className="w-full py-3 rounded-xl border border-border hover:bg-secondary transition">Kostenlos starten</button>
          </div>
          <div className="p-8 rounded-2xl border-2 border-primary/60 bg-card shadow-glow relative">
            <div className="absolute -top-3 right-6 px-3 py-1 rounded-full bg-gradient-primary text-primary-foreground text-xs font-medium">Empfohlen</div>
            <div className="text-sm text-accent mb-2">Pro</div>
            <div className="text-5xl font-bold mb-1">5€</div>
            <div className="text-sm text-muted-foreground mb-6">einmalig</div>
            <ul className="space-y-3 text-sm mb-8">
              {["Alles aus Free", "Branding entfernen", "Eigene Domain", "Prioritäts-Support"].map(x => (
                <li key={x} className="flex gap-2"><Check className="size-4 text-accent shrink-0 mt-0.5" />{x}</li>
              ))}
            </ul>
            <a href="mailto:hello@locallift.io?subject=Pro%20freischalten" className="block text-center w-full py-3 rounded-xl bg-gradient-primary text-primary-foreground font-medium shadow-glow hover:scale-105 transition">Pro freischalten</a>
          </div>
        </div>
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section className="py-32 px-6">
      <div className="max-w-4xl mx-auto text-center relative p-16 rounded-3xl border border-border bg-card/60 backdrop-blur overflow-hidden">
        <div className="absolute inset-0 grid-bg opacity-50" />
        <div className="relative">
          <div className="flex justify-center gap-1 mb-6">
            {[1,2,3,4,5].map(i => <Star key={i} className="size-5 fill-accent text-accent" />)}
          </div>
          <h2 className="text-4xl md:text-5xl font-bold mb-5">Bereit, dein Stadtviertel<br />online zu bringen?</h2>
          <p className="text-muted-foreground text-lg mb-8 max-w-xl mx-auto">
            Starte den ersten automatischen Scan und sieh in 60 Sekunden die ersten generierten Seiten.
          </p>
          <button onClick={openBackend("/")} className="bg-gradient-primary text-primary-foreground px-8 py-4 rounded-xl font-medium shadow-glow hover:scale-105 transition inline-flex items-center gap-2">
            Demo starten <ArrowRight className="size-4" />
          </button>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="py-12 px-6 border-t border-border">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <span className="size-6 rounded-md bg-gradient-primary grid place-items-center">
            <MapPin className="size-3 text-primary-foreground" />
          </span>
          <span className="font-display font-bold text-foreground">LocalLift</span>
          <span>© 2026</span>
        </div>
        <div className="flex gap-6">
          <a href="/impressum" className="hover:text-foreground transition">Impressum</a>
          <a href="/datenschutz" className="hover:text-foreground transition">Datenschutz</a>
          <a href="/agb" className="hover:text-foreground transition">AGB</a>
        </div>
      </div>
    </footer>
  );
}
