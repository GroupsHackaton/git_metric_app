import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
	input: "https://octopus-app-6mltj.ondigitalocean.app/openapi.json",
	output: "src/client",
	plugins: ["@tanstack/react-query"],
});
