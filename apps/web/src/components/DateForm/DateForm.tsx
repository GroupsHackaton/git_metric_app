import { useEffect, useState } from "react"
import { useForm, Controller } from "react-hook-form"
import { addDays, format } from "date-fns"
import DatePicker from "../DatePicker/DatePicker"
import { useDateContext } from "../../contexts/dateContext"

interface FormValues {
	startDate?: Date
	endDate?: Date
}

export default function DateForm() {
	const { control, watch } = useForm<FormValues>({
		defaultValues: { startDate: undefined, endDate: undefined },
	})

	const dateContext = useDateContext()

	const [startOpen, setStartOpen] = useState(false)
	const [endOpen, setEndOpen] = useState(false)

	const startDate = watch("startDate")
	const endDate = watch("endDate")

	useEffect(() => {
		if (startDate && endDate) {
			if (startDate > endDate) return
			dateContext.setDates(
				startDate ? format(startDate, "yyyy-MM-dd") : "",
				endDate ? format(endDate, "yyyy-MM-dd") : ""
			)
		}
	}, [startDate, endDate, dateContext])

	return (
		<div className="w-full flex gap-4 items-center justify-center md:flex-row flex-col">
			<div>
				<label className="block text-sm font-medium mb-1">Start Date</label>
				<Controller
					name="startDate"
					control={control}
					render={({ field }) => (
						<DatePicker
							{...field}
							open={startOpen}
							onOpenChange={setStartOpen}
							onSelect={(d) => {
								field.onChange(d)
								setStartOpen(false)
								setEndOpen(true)
							}}
							selected={field.value}
						/>
					)}
				/>
			</div>

			<div>
				<label className="block text-sm font-medium mb-1">End Date</label>
				<Controller
					name="endDate"
					control={control}
					render={({ field }) => (
						<DatePicker
							{...field}
							selected={field.value}
							open={endOpen}
							onOpenChange={setEndOpen}
							onSelect={(d) => {
								field.onChange(d)
								setEndOpen(false)
							}}
							disabled={
								startDate ? { before: addDays(startDate, 1) } : undefined
							}
						/>
					)}
				/>
			</div>
		</div>
	)
}
