import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useTheme } from "../../../lib/themeProvider"

export function DarkModeToggle() {
	const { theme, setTheme } = useTheme()

	const handleToggle = () => {
		setTheme(theme === "light" ? "dark" : "light")
	}

	return (
		<Button
			variant="outline"
			size="icon"
			onClick={handleToggle}
			aria-label="Toggle theme"
			className="relative overflow-hidden"
		>
			<Sun className="h-[1.2rem] w-[1.2rem] scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90" />
			<Moon
				className="absolute inset-0 m-auto h-[1.2rem] w-[1.2rem]
              transition-all
              scale-0 rotate-90
              dark:scale-100 dark:rotate-0"
			/>
		</Button>
	)
}
