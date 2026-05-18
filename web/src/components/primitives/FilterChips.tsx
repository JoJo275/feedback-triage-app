export interface FilterChipOption {
    value: string;
    label: string;
}

interface FilterChipsProps {
    ariaLabel: string;
    options: FilterChipOption[];
    activeValue: string;
    onChange: (value: string) => void;
}

export function FilterChips({
    ariaLabel,
    options,
    activeValue,
    onChange,
}: FilterChipsProps): JSX.Element {
    return (
        <div
            className="sn-react-filter-chips"
            role="group"
            aria-label={ariaLabel}
        >
            {options.map((option) => {
                const isActive = option.value === activeValue;

                return (
                    <button
                        key={option.value}
                        type="button"
                        className={`sn-filter-chip${isActive ? " is-active" : ""}`}
                        aria-pressed={isActive}
                        onClick={() => {
                            onChange(option.value);
                        }}
                    >
                        {option.label}
                    </button>
                );
            })}
        </div>
    );
}
