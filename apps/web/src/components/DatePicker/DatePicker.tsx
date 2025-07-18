import { format } from "date-fns"
import { Calendar as CalendarIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
	Popover,
	PopoverContent,
	PopoverTrigger,
} from "@/components/ui/popover"

export type DatePickerProps = {
	selected?: Date
	onSelect: (date: Date) => void
	placeholder?: string
	open?: boolean
	onOpenChange?: (open: boolean) => void
	disabled?: React.ComponentProps<typeof Calendar>["disabled"]
}

export default function DatePicker({
	selected,
	onSelect,
	placeholder = "Pick a date",
	open,
	onOpenChange,
	disabled,
}: DatePickerProps) {
	const label = selected ? format(selected, "PPP") : placeholder

	return (
		<Popover open={open} onOpenChange={onOpenChange}>
			<PopoverTrigger asChild>
				<Button
					variant="outline"
					className="
            data-[empty=true]:text-muted-foreground
            w-[280px] justify-start text-left font-normal
          "
				>
					<CalendarIcon className="mr-2 h-4 w-4" />
					<span>{label}</span>
				</Button>
			</PopoverTrigger>

			<PopoverContent className="w-auto p-0">
				<Calendar
					mode="single"
					selected={selected}
					onSelect={(date) => {
						if (date) onSelect(date)
					}}
					disabled={disabled}
				/>
			</PopoverContent>
		</Popover>
	)
}
