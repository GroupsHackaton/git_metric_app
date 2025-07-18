type route = {
	[key: string]: {
		path: string
		name: string
	}
}

const routes: route = {
	Home: {
		path: "/",
		name: "home",
	},
}

export default routes
