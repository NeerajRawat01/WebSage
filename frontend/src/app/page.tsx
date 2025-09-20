import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Search, Brain, MessageSquare, BarChart3, Zap, Shield, Globe, ArrowRight } from "lucide-react"

export default function HomePage() {
  const features = [
    {
      icon: Search,
      title: "Smart Web Scraping",
      description: "Advanced AI-powered extraction of website content and metadata",
    },
    {
      icon: Brain,
      title: "AI Analysis",
      description: "Deep insights about industry, company size, and business intelligence",
    },
    {
      icon: MessageSquare,
      title: "Conversational Interface",
      description: "Ask follow-up questions and get detailed explanations naturally",
    },
    {
      icon: BarChart3,
      title: "Session Management",
      description: "Track and revisit all your website analysis sessions",
    },
  ]

  const benefits = [
    { icon: Zap, text: "Lightning fast analysis" },
    { icon: Shield, text: "Secure and private" },
    { icon: Globe, text: "Works with any website" },
  ]

  return (
    <div className="relative overflow-hidden">
      {/* Background gradient overlays */}
      <div
        aria-hidden
        className="absolute inset-0 -z-10 bg-[radial-gradient(1200px_600px_at_50%_-120px,rgba(99,102,241,0.35)_0%,rgba(99,102,241,0)_60%),radial-gradient(800px_400px_at_10%_20%,rgba(168,85,247,0.22)_0%,rgba(168,85,247,0)_60%),linear-gradient(180deg,#0b1021_0%,#0a0f1e_100%)]"
      />
      {/* Subtle grid pattern (optional) */}
      <div className="absolute inset-0 grid-pattern opacity-20" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <section className="py-20 text-center">
          <div className="max-w-4xl mx-auto">
            <Badge variant="secondary" className="mb-6 bg-primary/10 text-primary border-primary/20">
              AI-Powered Website Intelligence
            </Badge>

            <h1 className="text-4xl md:text-6xl font-bold mb-6 text-balance">
              Unlock{" "}
              <span className="bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
                AI insights
              </span>{" "}
              from any website
            </h1>

            <p className="text-xl text-muted-foreground mb-8 text-pretty max-w-2xl mx-auto">
              Transform website analysis with AI-driven intelligence. Extract insights, ask questions, and get
              conversational answers about any website in seconds.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button size="lg" asChild className="bg-primary hover:bg-primary/90 text-primary-foreground">
                <Link href="/analyze" className="gap-2">
                  Start Analyzing
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </Button>

              <Button size="lg" variant="outline" asChild>
                <Link href="/sessions">View Sessions</Link>
              </Button>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section className="py-20">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Powerful Features</h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Everything you need to analyze websites with AI-powered intelligence
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon
              return (
                <Card
                  key={index}
                  className="border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-colors"
                >
                  <CardHeader>
                    <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                      <Icon className="w-6 h-6 text-primary" />
                    </div>
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-muted-foreground">{feature.description}</CardDescription>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </section>

        {/* Benefits Section */}
        <section className="py-20">
          <Card className="border-border/50 bg-card/30 backdrop-blur-sm">
            <CardContent className="p-8">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold mb-4">Why Choose WebSage?</h3>
                <p className="text-muted-foreground">Built for professionals who need reliable website intelligence</p>
              </div>

              <div className="flex flex-col md:flex-row justify-center items-center gap-8">
                {benefits.map((benefit, index) => {
                  const Icon = benefit.icon
                  return (
                    <div key={index} className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                        <Icon className="w-5 h-5 text-primary" />
                      </div>
                      <span className="font-medium">{benefit.text}</span>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </section>

        {/* CTA Section */}
        <section className="py-20 text-center">
          <div className="max-w-2xl mx-auto">
            <h3 className="text-3xl font-bold mb-4">Ready to get started?</h3>
            <p className="text-muted-foreground mb-8">Start analyzing websites with AI-powered insights today</p>

            <Button size="lg" asChild className="bg-primary hover:bg-primary/90">
              <Link href="/analyze" className="gap-2">
                Analyze Your First Website
                <ArrowRight className="w-4 h-4" />
              </Link>
            </Button>
          </div>
        </section>
      </div>
    </div>
  )
}
