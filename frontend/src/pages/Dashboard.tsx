import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingDown, TrendingUp, Package, Bell, Plus, ArrowRight } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useAuth } from "@/contexts/AuthContext";
import { ref, get } from "firebase/database";
import { db } from "@/services/firebase/firebase";

const Dashboard = () => {
  const { user, logout } = useAuth();

  const [products, setProducts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // 🧠 Fetch tracked products from Realtime DB (mock or actual)
  useEffect(() => {
    const fetchProducts = async () => {
      if (!user) return;
      try {
        const snapshot = await get(ref(db, `users/${user.uid}/products`));
        if (snapshot.exists()) {
          const data = Object.values(snapshot.val());
          setProducts(data);
        } else {
          setProducts([]);
        }
      } catch (error) {
        console.error("❌ Error fetching products:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProducts();
  }, [user]);

  const totalProducts = products.length;

  // Dashboard summary stats
  const stats = [
    {
      title: "Products Tracked",
      value: totalProducts.toString(),
      icon: Package,
      trend: `+${totalProducts}`,
      trendLabel: "active",
    },
    {
      title: "Active Alerts",
      value: "0", // can later be replaced by an alerts count
      icon: Bell,
      trend: "0",
      trendLabel: "triggered today",
    },
    {
      title: "Total Savings",
      value: "$0",
      icon: TrendingDown,
      trend: "+$0",
      trendLabel: "this week",
      positive: true,
    },
  ];

  // Recent price changes mock (you can later fetch from a price history node)
  const recentPriceChanges = products.slice(0, 3).map((product) => ({
    id: product.id || product.name,
    name: product.name || "Unnamed Product",
    image: product.image_url || "https://via.placeholder.com/400",
    currentPrice: product.current_price || 0,
    platform: product.platform || "Unknown",
  }));

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-muted-foreground">
              Welcome back, {user?.displayName || "User"}! Track your products and monitor price changes.
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={logout}>Logout</Button>
            <Button asChild>
              <NavLink to="/products/add">
                <Plus className="mr-2 h-4 w-4" />
                Add Product
              </NavLink>
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-6 md:grid-cols-3 mb-8">
          {stats.map((stat, index) => (
            <Card key={index} className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <stat.icon className="h-5 w-5 text-primary" />
                </div>
                {stat.positive !== undefined && (
                  <Badge
                    variant={stat.positive ? "default" : "secondary"}
                    className={stat.positive ? "bg-success" : ""}
                  >
                    {stat.trend}
                  </Badge>
                )}
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">{stat.title}</p>
                <p className="text-3xl font-bold">{stat.value}</p>
                <p className="text-xs text-muted-foreground">
                  {stat.trend} {stat.trendLabel}
                </p>
              </div>
            </Card>
          ))}
        </div>

        {/* Recent Price Changes */}
        <Card className="p-6">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-xl font-semibold">Recent Price Changes</h2>
            <Button variant="ghost" size="sm" asChild>
              <NavLink to="/products">
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </NavLink>
            </Button>
          </div>

          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-4 p-4">
                  <Skeleton className="h-16 w-16 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/4" />
                  </div>
                  <Skeleton className="h-8 w-24" />
                </div>
              ))}
            </div>
          ) : recentPriceChanges.length > 0 ? (
            <div className="space-y-4">
              {recentPriceChanges.map((product) => (
                <div
                  key={product.id}
                  className="flex items-center gap-4 p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors"
                >
                  <img
                    src={product.image}
                    alt={product.name}
                    className="h-16 w-16 rounded-lg object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = "https://via.placeholder.com/400";
                    }}
                  />
                  <div className="flex-1">
                    <h3 className="font-medium mb-1">{product.name}</h3>
                    <Badge variant="outline" className="text-xs">
                      {product.platform}
                    </Badge>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-2xl font-bold">${product.currentPrice.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No products tracked yet</p>
              <Button className="mt-4" asChild>
                <NavLink to="/products/add">
                  <Plus className="mr-2 h-4 w-4" />
                  Add Your First Product
                </NavLink>
              </Button>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
