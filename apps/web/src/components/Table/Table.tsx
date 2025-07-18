import { useQuery } from "@tanstack/react-query"
import { getCommitDeviationsCommitsDeviationsGetOptions } from "../../client/@tanstack/react-query.gen"
import { useDateContext } from "../../contexts/dateContext"
import {
	Table,
	TableHeader,
	TableHead,
	TableRow,
	TableBody,
	TableCell,
} from "../ui/table"

export default function DeviationsTable() {
	const { startDate, endDate } = useDateContext()

	const { data, isLoading, error } = useQuery({
		...getCommitDeviationsCommitsDeviationsGetOptions({
			query: {
				start_date: startDate,
				end_date: endDate,
			},
		}),
		enabled: Boolean(startDate && endDate),
	})
	if (!startDate || !endDate) {
		return <div className="text-gray-500">Please select a date range.</div>
	}

	if (isLoading) return <div>Loading deviations…</div>
	if (error) return <div className="text-red-600">Error loading data</div>

	return (
		<div className="w-full overflow-auto">
			<Table>
				<TableHeader>
					<TableRow>
						<TableHead>SHA</TableHead>
						<TableHead>Author</TableHead>
						<TableHead>Title</TableHead>
						<TableHead className="text-right">Additions</TableHead>
						<TableHead className="text-right">Deletions</TableHead>
						<TableHead className="text-right">Total Changes</TableHead>
						<TableHead className="text-right">Z‑Score</TableHead>
					</TableRow>
				</TableHeader>
				<TableBody>
					{(data || []).map((commit) => (
						<TableRow key={commit.sha}>
							<TableCell>
								<a
									href={`https://github.com/OpenRA/OpenRA/commit/${commit.sha}`}
									target="_blank"
									rel="noopener noreferrer"
									className="font-mono text-sm text-blue-600 hover:underline"
								>
									{commit.sha.slice(0, 7)}
								</a>
							</TableCell>
							<TableCell className="font-mono text-sm">
								{commit.author_name}
							</TableCell>
							<TableCell className="max-w-xs truncate">
								{commit.title}
							</TableCell>
							<TableCell className="text-right">{commit.additions}</TableCell>
							<TableCell className="text-right">{commit.deletions}</TableCell>
							<TableCell className="text-right">
								{commit.total_changes}
							</TableCell>
							<TableCell className="text-right">
								{commit.z_score.toFixed(2)}
							</TableCell>
						</TableRow>
					))}
				</TableBody>
			</Table>
		</div>
	)
}
