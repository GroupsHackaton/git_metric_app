import { getWordFrequencyCommitsWordFrequencyGetOptions } from "@/client/@tanstack/react-query.gen"
import { useQuery } from "@tanstack/react-query"
import ReactWordCloud, { type Word } from "react-wordcloud"
import { useDateContext } from "@/contexts/dateContext"

export default function WordCloud() {
	const { startDate, endDate } = useDateContext()
	const { data } = useQuery({
		...getWordFrequencyCommitsWordFrequencyGetOptions({
			query: { end_date: endDate, start_date: startDate },
		}),
		enabled: !!endDate && !!startDate,
	})

	const words: Word[] = Object.entries(data ?? {})
		.map(([text, value]) => ({ text, value }))
		.slice(0, 12)

	return (
		<ReactWordCloud
			words={words}
			minSize={[10, 19]}
			options={{
				fontFamily: "Courier New",
				fontWeight: "bold",
				padding: 1,
				scale: "log",
				fontSizes: [10, 60],
				colors: ["#4A90E2", "#50E3C2", "#F5A623", "#D0021B"],
				rotations: 2,
			}}
		/>
	)
}
