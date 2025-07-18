import { BrowserRouter } from "react-router"
import { Router } from "./router"
import { ThemeProvider } from "./lib/themeProvider"

function App() {
	return (
		<ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
			<BrowserRouter>
				<Router />
			</BrowserRouter>
		</ThemeProvider>
	)
}

export default App
