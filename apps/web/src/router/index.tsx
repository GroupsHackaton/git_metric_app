import { Route, Routes } from "react-router"
import routes from "./routeList"

import Home from "../../Pages/Home/Home"

export const Router = () => {
	return (
		<Routes>
			<Route path={routes.Home.path} element={<Home />} />

			<Route path="*" element={<>404</>} />
		</Routes>
	)
}
