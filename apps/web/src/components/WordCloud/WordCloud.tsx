import { getWordFrequencyCommitsWordFrequencyGetOptions } from "@/client/@tanstack/react-query.gen"
import { useQuery } from "@tanstack/react-query"
import {
	WordCloud as ReactWordCloud,
	type Word,
} from "@isoterik/react-word-cloud"
import { useDateContext } from "@/contexts/dateContext"

export default function WordCloud() {
	const dateContext = useDateContext()
	const { data } = useQuery({
		...getWordFrequencyCommitsWordFrequencyGetOptions({
			query: {
				end_date: dateContext.endDate,
				start_date: dateContext.startDate,
			},
		}),
		enabled: dateContext.endDate.length > 0 && dateContext.startDate.length > 0,
	})
	const words: Word[] = Object.entries(data ?? {})
		.map((item) => ({
			text: item[0],
			value: item[1],
		}))
		.slice(0, 12)
	return <ReactWordCloud words={words} width={500} height={200} fontSize={20} />
}
