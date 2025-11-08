import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Search,
  Plus,
  TrendingDown,
  TrendingUp,
  ExternalLink,
  Package,
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { productsApi, Product } from "@/lib/api";

const Products = () => {
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch products (uses your api.ts)
  const { data, isLoading, error } = useQuery({
    queryKey: ["products", { search: searchQuery || undefined }],
    queryFn: () =>
      productsApi.list({
        search: searchQuery || undefined,
        limit: 50,
      }),
  });

  const products = data?.items || [];

  const formatPrice = (price?: number, currency: string = "USD") => {
    if (!price) return "N/A";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
    }).format(price);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight mb-2">Products</h1>
          <p className="text-muted-foreground">
            Manage and track your product prices
          </p>
        </div>

        {/* Search + Add */}
        <div className="mb-8 flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button asChild>
            <NavLink to="/products/add">
              <Plus className="mr-2 h-4 w-4" />
              Add Product
            </NavLink>
          </Button>
        </div>

        {/* Error State */}
        {error && (
          <Card className="p-6 mb-6 border-destructive">
            <p className="text-destructive">
              Failed to load products. Please try again later.
            </p>
          </Card>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <Card key={i} className="overflow-hidden">
                <Skeleton className="aspect-square w-full" />
                <div className="p-6 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-8 w-full" />
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Products Grid */}
        {!isLoading && products.length > 0 && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {products.map((product: Product) => {
              const priceChange = 0; // Placeholder for future trend logic

              return (
                <Card
                  key={product.id}
                  className="overflow-hidden hover:shadow-lg transition-shadow"
                >
                  <div className="aspect-square relative bg-muted">
                    {product.image_url ? (
                      <img
                        src={product.image_url}
                        alt={product.name}
                        className="h-full w-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src =
                            "https://via.placeholder.com/400";
                        }}
                      />
                    ) : (
                      <div className="h-full w-full flex items-center justify-center text-muted-foreground">
                        <Package className="h-12 w-12" />
                      </div>
                    )}
                    <Badge className="absolute top-3 right-3 bg-background/80 backdrop-blur">
                      {product.platform}
                    </Badge>
                    {product.is_tracking && (
                      <Badge className="absolute top-3 left-3 bg-primary/80 backdrop-blur">
                        Tracking
                      </Badge>
                    )}
                  </div>

                  <div className="p-6">
                    <div className="mb-2">
                      {product.category && (
                        <Badge variant="outline" className="text-xs mb-2">
                          {product.category}
                        </Badge>
                      )}
                      <h3 className="font-semibold line-clamp-2 mb-1">
                        {product.name}
                      </h3>
                      {product.brand && (
                        <p className="text-sm text-muted-foreground">
                          {product.brand}
                        </p>
                      )}
                    </div>

                    <div className="mb-4">
                      <div className="flex items-baseline gap-2 mb-1">
                        <span className="text-2xl font-bold">
                          {formatPrice(product.current_price, product.currency)}
                        </span>
                        {priceChange !== 0 && (
                          <div className="flex items-center gap-1">
                            {priceChange < 0 ? (
                              <TrendingDown className="h-4 w-4 text-success" />
                            ) : (
                              <TrendingUp className="h-4 w-4 text-warning" />
                            )}
                            <span
                              className={
                                priceChange < 0
                                  ? "text-success text-sm font-medium"
                                  : "text-warning text-sm font-medium"
                              }
                            >
                              {Math.abs(priceChange)}%
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button className="flex-1" size="sm" asChild>
                        <NavLink to={`/products/${product.id}`}>
                          View Details
                        </NavLink>
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          window.open(product.product_url, "_blank")
                        }
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && products.length === 0 && (
          <Card className="p-12 text-center">
            <Package className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
            <h3 className="text-lg font-semibold mb-2">No products found</h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery
                ? "Try adjusting your search terms"
                : "Start tracking prices by adding your first product"}
            </p>
            <Button asChild>
              <NavLink to="/products/add">
                <Plus className="mr-2 h-4 w-4" />
                Add Product
              </NavLink>
            </Button>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Products;
