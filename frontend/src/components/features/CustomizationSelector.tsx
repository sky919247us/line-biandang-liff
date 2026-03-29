/**
 * 客製化群組選擇器
 *
 * 支援單選、多選、數量選擇的客製化群組 UI
 */
import type { CustomizationGroup, CustomizationOption, SelectedCustomization } from '../../types';
import './CustomizationSelector.css';

interface CustomizationSelectorProps {
    groups: CustomizationGroup[];
    /** Ungrouped legacy options (no group_id) */
    ungroupedOptions: CustomizationOption[];
    selectedCustomizations: SelectedCustomization[];
    onChange: (customizations: SelectedCustomization[]) => void;
}

export function CustomizationSelector({
    groups,
    ungroupedOptions,
    selectedCustomizations,
    onChange,
}: CustomizationSelectorProps) {
    const isSelected = (optId: string) => selectedCustomizations.some(c => c.id === optId);

    const handleToggle = (opt: CustomizationOption, group?: CustomizationGroup) => {
        const selected: SelectedCustomization = {
            id: opt.id,
            name: opt.name,
            price: opt.priceAdjustment,
        };

        if (group?.groupType === 'single_select') {
            // Single select: replace within group
            const otherGroupOptionIds = group.options.map(o => o.id);
            const withoutGroup = selectedCustomizations.filter(c => !otherGroupOptionIds.includes(c.id));
            if (isSelected(opt.id)) {
                // Deselect only if not required
                if (!group.isRequired) {
                    onChange(withoutGroup);
                }
            } else {
                onChange([...withoutGroup, selected]);
            }
        } else if (group?.groupType === 'multi_select') {
            // Multi select: toggle, respect max
            if (isSelected(opt.id)) {
                onChange(selectedCustomizations.filter(c => c.id !== opt.id));
            } else {
                const currentGroupCount = selectedCustomizations.filter(c =>
                    group.options.some(o => o.id === c.id)
                ).length;
                if (group.maxSelect > 0 && currentGroupCount >= group.maxSelect) {
                    return; // Max reached
                }
                onChange([...selectedCustomizations, selected]);
            }
        } else {
            // Legacy toggle (ungrouped)
            if (isSelected(opt.id)) {
                onChange(selectedCustomizations.filter(c => c.id !== opt.id));
            } else {
                onChange([...selectedCustomizations, selected]);
            }
        }
    };

    return (
        <div className="customization-selector">
            {/* Grouped options */}
            {groups.map(group => (
                <div key={group.id} className="customization-group">
                    <div className="customization-group__header">
                        <h4 className="customization-group__title">
                            {group.name}
                            {group.isRequired && <span className="customization-group__required">必選</span>}
                        </h4>
                        <span className="customization-group__hint">
                            {group.groupType === 'single_select' && '單選'}
                            {group.groupType === 'multi_select' && (
                                group.maxSelect > 0
                                    ? `可選 ${group.minSelect}-${group.maxSelect} 項`
                                    : `至少選 ${group.minSelect} 項`
                            )}
                        </span>
                    </div>
                    <div className="customization-group__options">
                        {group.options.map(opt => {
                            const selected = isSelected(opt.id);
                            const isRadio = group.groupType === 'single_select';
                            return (
                                <label
                                    key={opt.id}
                                    className={`customization-option ${selected ? 'active' : ''}`}
                                >
                                    <input
                                        type={isRadio ? 'radio' : 'checkbox'}
                                        name={isRadio ? `group-${group.id}` : undefined}
                                        checked={selected}
                                        onChange={() => handleToggle(opt, group)}
                                    />
                                    <span className="customization-option__name">{opt.name}</span>
                                    {opt.priceAdjustment > 0 && (
                                        <span className="customization-option__price">+${opt.priceAdjustment}</span>
                                    )}
                                </label>
                            );
                        })}
                    </div>
                </div>
            ))}

            {/* Ungrouped legacy options */}
            {ungroupedOptions.length > 0 && (
                <div className="customization-group">
                    <div className="customization-group__header">
                        <h4 className="customization-group__title">其他選項</h4>
                    </div>
                    <div className="customization-group__options">
                        {ungroupedOptions.map(opt => {
                            const selected = isSelected(opt.id);
                            return (
                                <label
                                    key={opt.id}
                                    className={`customization-option ${selected ? 'active' : ''}`}
                                >
                                    <input
                                        type="checkbox"
                                        checked={selected}
                                        onChange={() => handleToggle(opt)}
                                    />
                                    <span className="customization-option__name">{opt.name}</span>
                                    {opt.priceAdjustment > 0 && (
                                        <span className="customization-option__price">+${opt.priceAdjustment}</span>
                                    )}
                                </label>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}

export default CustomizationSelector;
