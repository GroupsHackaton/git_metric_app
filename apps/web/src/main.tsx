import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DateContextProvider } from "./contexts/dateContext.tsx";

const queryClient = new QueryClient();
createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<QueryClientProvider client={queryClient}>
			<DateContextProvider>
				<App />
			</DateContextProvider>
		</QueryClientProvider>
	</StrictMode>
);
