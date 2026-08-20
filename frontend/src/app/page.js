import NavBar from "@/components/layout/NavBar";
import Footer from "@/components/layout/Footer";
import Section from "@/components/layout/Section";
import SectionHeading from "@/components/layout/SectionHeading";
import StatStrip from "@/components/marketing/StatStrip";
import StepDiagram from "@/components/marketing/StepDiagram";
import FAQAccordion from "@/components/marketing/FAQAccordion";
import MapCanvasLoader from "@/components/map/MapCanvasLoader";
import RoutePlanner from "@/components/map/RoutePlanner";
import ReportFlowDemo from "@/components/report/ReportFlowDemo";
import VerificationExplainer from "@/components/verification/VerificationExplainer";
import ChatPanel from "@/components/chat/ChatPanel";
import ReportReviewScreen from "@/components/authority/ReportReviewScreen";
import SyncStatusBadge from "@/components/authority/SyncStatusBadge";
import {
  getReports,
  getClusters,
  getStats,
  getAuthorityReport,
  getSyncStatus,
} from "@/lib/api";

const REPORT_STEPS = [
  {
    title: "Report",
    description:
      "A citizen files a hazard report with a category, description, and location.",
  },
  {
    title: "Cluster",
    description:
      "Nearby reports of the same hazard are grouped into a candidate cluster.",
  },
  {
    title: "Consensus",
    description:
      "Each distinct reporter raises the cluster's confidence score.",
  },
  {
    title: "Verified",
    description:
      "At 60+ confidence the cluster is verified and routed toward authorities.",
  },
];

const FAQ_ITEMS = [
  {
    question: "What counts as a report?",
    answer:
      "Any hazard a citizen can see and categorize — flooding, road damage, unsafe construction, and more — with a short description and a location.",
  },
  {
    question: "How is a report verified?",
    answer:
      "Reports of the same hazard near each other are grouped into a cluster. Each distinct reporter who confirms it raises the cluster's confidence score; at 60+ it's marked verified.",
  },
  {
    question: "Is my location shared?",
    answer:
      "Only the report's location is shared, not your identity. Your trust score is tracked internally to weight consensus, not shown publicly against your name.",
  },
  {
    question: "What happens after a report is verified?",
    answer:
      "The Authority Agent drafts a structured complaint from the verified cluster. A human reviewer approves it before it's sent to the identified authority.",
  },
];

// Server Component: fetches everything the page needs once, then hands
// plain data down to presentational or client components. Each `get*` call
// transparently falls back to demo fixtures if no backend is configured —
// see lib/api.js.
export default async function Home() {
  const [reportsRes, clustersRes, statsRes, authorityRes, syncRes] =
    await Promise.all([
      getReports(),
      getClusters(),
      getStats(),
      getAuthorityReport("c-201"),
      getSyncStatus(),
    ]);

  return (
    <div id="top" className="flex flex-1 flex-col font-body">
      <NavBar />

      <main className="flex flex-1 flex-col">
        {/* Hero 1 — Landing / value prop */}
        <Section tone="paper">
          <div className="grid grid-cols-1 items-end gap-12 lg:grid-cols-[1.2fr_0.8fr]">
            <div>
              <p className="mb-5 font-mono text-xs uppercase tracking-[0.18em] text-hazard">
                Crowdsourced hazard verification
              </p>
              <h1 className="font-display text-5xl font-bold leading-[1.05] tracking-tight sm:text-6xl">
                One report is a rumor.
                <br />
                Nine reports are a{" "}
                <span className="text-verified">verified hotspot</span>.
              </h1>
              <p className="mt-6 max-w-lg text-lg leading-relaxed opacity-80">
                VeriGrid crowdsources citizen hazard reports, confirms them
                through independent-reporter consensus, layers in MirEye
                infrastructure data, and routes verified issues straight to the
                authority responsible.
              </p>
              <div className="mt-8 flex flex-wrap gap-4">
                <a
                  href="#report"
                  className="rounded-sm bg-hazard px-6 py-3 font-mono text-xs uppercase tracking-[0.1em] text-ink-text transition-opacity hover:opacity-90"
                >
                  Report an issue
                </a>
                <a
                  href="#map"
                  className="rounded-sm border border-paper-text/30 px-6 py-3 font-mono text-xs uppercase tracking-[0.1em] transition-colors hover:border-paper-text"
                >
                  Explore the map
                </a>
              </div>
            </div>
            <div className="rounded-sm border border-line bg-paper-2/60 p-6">
              <StatStrip stats={statsRes.data} />
            </div>
          </div>
        </Section>

        {/* Hero 2 — Live map */}
        <Section id="map" tone="ink">
          <SectionHeading
            eyebrow="The live product"
            eyebrowColor="var(--color-hazard)"
            title="The map, as it actually looks right now"
            description="Raw reports, candidate clusters, and verified hotspots — filterable by category, with click-to-report built into the map itself."
          />
          <div className="mt-10">
            <MapCanvasLoader
              reports={reportsRes.data}
              clusters={clustersRes.data}
            />
          </div>
        </Section>

        {/* Hero 3 — Report flow */}
        <Section id="report" tone="paper">
          <SectionHeading
            eyebrow="Filing a report"
            eyebrowColor="var(--color-hazard)"
            title="From one tap to a verified hotspot"
            description="Every report enters the same pipeline: filed, clustered against nearby reports, confirmed by consensus, then verified."
          />
          <div className="mt-10">
            <StepDiagram steps={REPORT_STEPS} />
          </div>
          <div className="mt-10 max-w-lg">
            <ReportFlowDemo />
          </div>
        </Section>

        {/* Hero 4 — How verification works */}
        <Section id="how-it-works" tone="ink">
          <SectionHeading
            eyebrow="The consensus engine"
            eyebrowColor="var(--color-verified)"
            title="Verification is a vote, not a vibe"
            description="No single report can flip a location to verified. Confidence only climbs when distinct reporters independently confirm the same hazard — and confirming one earns you trust."
          />
          <div className="mt-10 max-w-xl">
            <VerificationExplainer />
          </div>
        </Section>

        {/* Hero 5 — Ask VeriGrid */}
        <Section id="ask" tone="paper">
          <SectionHeading
            eyebrow="Ask before you go"
            eyebrowColor="var(--color-amber)"
            title="Ask VeriGrid about any point on the map"
            description="Answers are grounded in two sources, and the panel always tells you which one: verified citizen reports, or MirEye's infrastructure records."
          />
          <div className="mt-10 max-w-xl">
            <ChatPanel />
          </div>
        </Section>

        {/* Hero 6 — Safe routing */}
        <Section tone="paper2">
          <SectionHeading
            eyebrow="Getting there safely"
            eyebrowColor="var(--color-verified)"
            title="Routes that detour around verified hazards"
            description="Plan a route and VeriGrid checks it against verified hotspots along the corridor, rerouting when one sits in the way."
          />
          <div className="mt-10">
            <RoutePlanner />
          </div>
        </Section>

        {/* Hero 7 — For authorities */}
        <Section id="authorities" tone="ink">
          <SectionHeading
            eyebrow="For authorities"
            eyebrowColor="var(--color-amber)"
            title="A verified cluster, drafted as a complaint"
            description="Once a cluster is verified, the Authority Agent drafts a structured complaint and routes it to the responsible office — a human reviewer approves before anything is sent."
          />
          <div className="mt-10 max-w-2xl">
            <ReportReviewScreen initialReport={authorityRes.data} />
          </div>
        </Section>

        {/* Hero 8 — MirEye integration / trust */}
        <Section tone="paper">
          <SectionHeading
            eyebrow="What powers this"
            eyebrowColor="var(--color-verified)"
            title="Layered on MirEye infrastructure data"
            description="Area context and verified observations sync in from MirEye, so answers and authority routing are grounded in real infrastructure records, not just citizen reports alone."
          />
          <div className="mt-8">
            <SyncStatusBadge sync={syncRes.data} />
          </div>
        </Section>

        {/* FAQ */}
        <Section id="faq" tone="paper2">
          <SectionHeading title="Frequently asked" align="center" />
          <div className="mx-auto mt-10 max-w-2xl">
            <FAQAccordion items={FAQ_ITEMS} />
          </div>
        </Section>
      </main>

      <Footer />
    </div>
  );
}
