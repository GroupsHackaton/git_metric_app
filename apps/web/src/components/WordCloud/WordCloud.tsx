import { getWordFrequencyCommitsWordFrequencyGetOptions } from "@/client/@tanstack/react-query.gen";
import { useQuery } from "@tanstack/react-query";
import { useDateContext } from "@/contexts/dateContext";
import {
	type Word,
	WordCloud as ReactWordCloud,
} from "@isoterik/react-word-cloud";
export default function WordCloud() {
	const { startDate, endDate } = useDateContext();
	const { data } = useQuery({
		...getWordFrequencyCommitsWordFrequencyGetOptions({
			query: { end_date: endDate, start_date: startDate },
		}),
		enabled: !!endDate && !!startDate,
	});

	const words: Word[] = Object.entries(data ?? {})
		.map(([text, value]) => ({ text, value }))
		.slice(0, 12);
	console.log(words);
	return (
		<ReactWordCloud
			words={words}
			width={300}
			height={200}
			fontSize={(word) => 5 + word.value * 2}
		/>
	);
}
