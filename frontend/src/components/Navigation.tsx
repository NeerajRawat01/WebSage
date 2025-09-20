"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { BarChart3, Home, Search, History } from "lucide-react"

export function Navigation() {
    const pathname = usePathname()

    const navItems = [
        { href: "/", label: "Home", icon: Home },
        { href: "/analyze", label: "Analyze", icon: Search },
        { href: "/sessions", label: "Sessions", icon: History },
    ]

    return (
        <nav className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    <Link href="/" className="flex items-center gap-2 font-bold text-xl">
                        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                            <BarChart3 className="w-5 h-5 text-primary-foreground" />
                        </div>
                        <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">WebSage</span>
                    </Link>

                    <div className="flex items-center gap-1">
                        {navItems.map((item) => {
                            const Icon = item.icon
                            const isActive = pathname === item.href

                            return (
                                <Button
                                    key={item.href}
                                    variant={isActive ? "secondary" : "ghost"}
                                    size="sm"
                                    asChild
                                    className={cn("gap-2", isActive && "bg-primary/10 text-primary hover:bg-primary/20")}
                                >
                                    <Link href={item.href}>
                                        <Icon className="w-4 h-4" />
                                        {item.label}
                                    </Link>
                                </Button>
                            )
                        })}
                    </div>
                </div>
            </div>
        </nav>
    )
}
