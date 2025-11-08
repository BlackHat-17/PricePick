import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingDown, Bell, LineChart, Search, Shield, Zap } from "lucide-react";
import { NavLink } from "@/components/NavLink";

const Landing = () => {
  const features = [
    {
      icon: Search,
      title: "Multi-Platform Tracking",
      description: "Track prices across Amazon, eBay, Walmart, and more from a single dashboard."
    },
    {
      icon: LineChart,
      title: "Price History Charts",
      description: "Visualize price trends over time and identify the perfect moment to buy."
    },
    {
      icon: Bell,
      title: "Smart Alerts",
      description: "Get instant notifications when prices drop below your target."
    },
    {
      icon: Shield,
      title: "Secure & Private",
      description: "Your data is encrypted and never shared with third parties."
    },
    {
      icon: Zap,
      title: "Real-Time Updates",
      description: "Prices are checked multiple times daily for accurate tracking."
    },
    {
      icon: TrendingDown,
      title: "Best Deals",
      description: "Discover trending products and the biggest price drops."
    }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary/5 via-accent/5 to-background py-20 md:py-32">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-4xl text-center">
            <Badge className="mb-4 bg-primary/10 text-primary hover:bg-primary/20" variant="secondary">
              Track Smarter, Save More
            </Badge>
            <h1 className="mb-6 text-4xl font-bold tracking-tight md:text-6xl lg:text-7xl">
              Never Miss a
              <span className="block bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                Price Drop Again
              </span>
            </h1>
            <p className="mb-8 text-lg text-muted-foreground md:text-xl">
              Track product prices across multiple e-commerce platforms, get instant alerts,
              and make informed purchase decisions with comprehensive price history.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" asChild className="text-lg">
                <NavLink to="/signup">Start Tracking Free</NavLink>
              </Button>
              <Button size="lg" variant="outline" asChild className="text-lg">
                <NavLink to="/dashboard">View Demo</NavLink>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 md:py-32">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-2xl text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight md:text-4xl mb-4">
              Everything You Need to Save Money
            </h2>
            <p className="text-lg text-muted-foreground">
              Powerful features to help you track prices and never overpay again.
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => (
              <Card key={index} className="p-6 hover:shadow-lg transition-shadow">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mb-2 text-xl font-semibold">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="border-y bg-muted/50 py-16">
        <div className="container mx-auto px-4">
          <div className="grid gap-8 md:grid-cols-3 text-center">
            <div>
              <div className="text-4xl font-bold text-primary mb-2">10K+</div>
              <div className="text-muted-foreground">Products Tracked</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-success mb-2">$250K+</div>
              <div className="text-muted-foreground">Total Savings</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-accent mb-2">5K+</div>
              <div className="text-muted-foreground">Happy Users</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 md:py-32">
        <div className="container mx-auto px-4">
          <Card className="overflow-hidden bg-gradient-to-br from-primary/10 via-accent/10 to-background">
            <div className="p-8 md:p-16 text-center">
              <h2 className="text-3xl font-bold tracking-tight md:text-4xl mb-4">
                Ready to Start Saving?
              </h2>
              <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
                Join thousands of smart shoppers who never overpay. Start tracking prices for free today.
              </p>
              <Button size="lg" asChild>
                <NavLink to="/signup">Get Started Now</NavLink>
              </Button>
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
};

export default Landing;
