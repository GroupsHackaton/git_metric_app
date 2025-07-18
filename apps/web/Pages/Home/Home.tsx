import { useQuery } from "@tanstack/react-query"
import { Chart } from "../../src/components/Chart/Chart"
import DateForm from "../../src/components/DateForm/DateForm"
import Table from "../../src/components/Table/Table"
import { DarkModeToggle } from "../../src/components/ui/darkModeToggle/DarkModeToggle"
import { getWordFrequencyCommitsWordFrequencyGetOptions } from "../../src/client/@tanstack/react-query.gen"
export default function Home() {
	const { data } = useQuery(getWordFrequencyCommitsWordFrequencyGetOptions())

	console.log(data)
	return (
		<>
			<header className="flex items-center justify-between p-4">
				<DarkModeToggle />
			</header>

			<div className="w-full">
				<DateForm />
				<hr className="my-4" />
				<div className="flex items-center">
					<div className="w-1/2 flex items-center border-r ">
						<Table />
					</div>
					<div className="w-1/2 flex flex-col justify-center items-center  border-l">
						<div className="">
							<Chart />
						</div>
						<div className=""></div>
					</div>
				</div>
			</div>
		</>
	)
}
