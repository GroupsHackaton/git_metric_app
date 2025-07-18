import { createContext, useState, type PropsWithChildren } from "react";

export interface DateContext {
	startDate: string;
	endDate: string;
	setDates: (start: string, end: string) => void;
}
const dateContext = createContext<DateContext>({
	startDate: "",
	endDate: "",
	setDates: null!,
});

export const DateContextProvider = (props: PropsWithChildren) => {
	const [dates, setDates] = useState<Omit<DateContext, "setDates">>({
		endDate: "",
		startDate: "",
	});
	const setDatesFunc = (start: string, end: string) => {
		setDates({
			endDate: end,
			startDate: start,
		});
	};
	return (
		<dateContext.Provider
			value={{
				...dates,
				setDates: setDatesFunc,
			}}
		>
			{props.children}
		</dateContext.Provider>
	);
};
