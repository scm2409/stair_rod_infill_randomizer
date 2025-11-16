# Implementation Plan (Visual-First Approach)

This document outlines the implementation tasks following a **vertical slice** approach where you can see visual results early and approve each feature incrementally.

## Strategy

Build thin vertical slices through all layers:
1. **Slice 1**: Basic UI + Simple shape visualization
2. **Slice 2**: Add generator + See first infill results  
3. **Slice 3**: Add quality evaluation + See improved results
4. **Slice 4**: Add remaining features (BOM, save/load, etc.)

## Task List

### Phase 1: Foundation + Basic Visualization (See shapes immediately!)

- [x] 1. Set up project structure and core infrastructure
  - ✅ COMPLETED
  - _Requirements: 10, 11_

- [-] 2. Create minimal UI skeleton to see shapes
  - [x] 2.1 Implement Rod class (Pydantic BaseModel) - needed for shapes
    - Define fields: geometry (LineString), start_cut_angle_deg, end_cut_angle_deg, weight_kg_m, layer
    - Implement computed fields: length_cm, weight_kg, start_point, end_point
    - Write unit tests for Rod class
    - _Requirements: 1, 5, 6, 8_
  
  - [ ] 2.2 Create basic Main Window with viewport
    - Create MainWindow class (QMainWindow) with menu bar
    - Create ViewportWidget (QGraphicsView/QGraphicsScene)
    - Implement zoom and pan
    - Write test to verify window and viewport creation
    - **VISUAL MILESTONE**: Empty window with working viewport ✅
    - _Requirements: 7, 7.2_
  
  - [ ] 2.3 Implement StairShape (first shape to visualize!)
    - Create StairShapeDefaults dataclass
    - Create StairShapeParameters Pydantic model
    - Implement `get_boundary()` and `get_frame_rods()`
    - Write unit tests for StairShape
    - _Requirements: 2, 4, 5_
  
  - [ ] 2.4 Connect shape to viewport rendering
    - Implement frame rendering in viewport (render rods as lines)
    - Hard-code a StairShape instance for now
    - **VISUAL MILESTONE**: See your first stair shape! 🎉
    - Write test to verify frame rendering
    - _Requirements: 7, 7.1_

### Phase 2: Add Shape Selection (Choose and see different shapes!)

- [ ] 3. Add shape selection UI
  - [ ] 3.1 Implement RectangularShape
    - Create RectangularShapeDefaults dataclass
    - Create RectangularShapeParameters Pydantic model  
    - Implement `get_boundary()` and `get_frame_rods()`
    - Write unit tests for RectangularShape
    - _Requirements: 3, 4, 5_
  
  - [ ] 3.2 Create Shape factory and base class
    - Define abstract Shape base class
    - Implement factory to create shapes from type string
    - Write tests for factory and base class
    - _Requirements: 4_
  
  - [ ] 3.3 Add parameter panel for shape selection
    - Create ParameterPanel widget with shape type dropdown
    - Add "Update Shape" button
    - Connect to viewport to render selected shape
    - **VISUAL MILESTONE**: Switch between stair and rectangular shapes! 🎉
    - Write test to verify panel and shape switching
    - _Requirements: 5, 6, 7_

### Phase 3: First Infill Generation (See rods being generated!)

- [ ] 4. Implement simple random generator (without quality evaluation)
  - [ ] 4.1 Create InfillResult class
    - Define fields: rods (list), fitness_score (optional), iteration_count (optional)
    - Write unit tests
    - _Requirements: 1, 6.2, 9_
  
  - [ ] 4.2 Implement basic RandomGenerator (simplified version)
    - Create Generator base class with signals
    - Implement RandomGenerator with simple random placement
    - No quality evaluation yet - just generate random valid arrangements
    - Respect basic constraints (no crossings in same layer, within boundary)
    - Write unit tests for generator
    - _Requirements: 1, 4.1, 6.1, 9_
  
  - [ ] 4.3 Add generator UI and connect to viewport
    - Add generator type dropdown to parameter panel
    - Add "Generate Infill" button
    - Implement infill rendering in viewport (with layer colors)
    - **VISUAL MILESTONE**: See your first random infill! 🎉
    - Write test to verify infill rendering
    - _Requirements: 6.1, 7, 9_
  
  - [ ] 4.4 Add progress dialog for generation
    - Create ProgressDialog showing iteration count
    - Implement worker thread pattern for background generation
    - **VISUAL MILESTONE**: See generation progress in real-time! 🎉
    - Write test to verify progress dialog
    - _Requirements: 9.1, 9.1.1_

### Phase 4: Improve Quality (See better results!)

- [ ] 5. Add quality evaluation to improve results
  - [ ] 5.1 Implement hole identification
    - Implement function using `shapely.node()` and `polygonize()`
    - Write unit tests for hole identification
    - _Requirements: 6.2, 6.2.1_
  
  - [ ] 5.2 Implement quality criteria
    - Implement hole uniformity, incircle uniformity, angle distribution, anchor spacing
    - Write unit tests for each criterion
    - _Requirements: 6.2.1_
  
  - [ ] 5.3 Implement QualityEvaluator
    - Create EvaluatorCriteriaDefaults dataclass
    - Implement `evaluate()` and `is_acceptable()` methods
    - Write unit tests for evaluator
    - _Requirements: 6.2, 6.2.1_
  
  - [ ] 5.4 Connect evaluator to RandomGenerator
    - Update RandomGenerator to use QualityEvaluator
    - Add iteration limits and fitness-based termination
    - Update progress dialog to show fitness score
    - **VISUAL MILESTONE**: See quality improving over iterations! 🎉
    - Write integration tests
    - _Requirements: 1.1, 6.2, 6.3, 9.1.1_

### Phase 5: Add Parameter Controls (Fine-tune what you see!)

- [ ] 6. Add full parameter controls
  - [ ] 6.1 Implement dynamic parameter forms
    - Add shape parameter inputs (QDoubleSpinBox, QSpinBox)
    - Add generator parameter inputs
    - Show/hide based on selected type
    - Load defaults from Hydra config
    - **VISUAL MILESTONE**: Adjust parameters and see changes! 🎉
    - Write tests for parameter forms
    - _Requirements: 5, 6, 6.1, 10_
  
  - [ ] 6.2 Implement parameter validation
    - Connect Pydantic validation to UI
    - Display inline error messages
    - Write tests for validation display
    - _Requirements: 5, 9.2_

### Phase 6: Add BOM Table (See the parts list!)

- [ ] 7. Implement BOM table
  - [ ] 7.1 Create BOM Table widget
    - Create BOMTableWidget with two tabs (Frame/Infill)
    - Set up columns and sorting
    - Write test for table structure
    - _Requirements: 8_
  
  - [ ] 7.2 Populate BOM data
    - Populate from shape and infill result
    - Calculate and display totals
    - **VISUAL MILESTONE**: See parts list with totals! 🎉
    - Write tests for data population and totals
    - _Requirements: 8_
  
  - [ ] 7.3 Add BOM selection highlighting
    - Connect row selection to viewport highlighting
    - **VISUAL MILESTONE**: Click BOM row to highlight part! 🎉
    - Write test for selection
    - _Requirements: 8.1_

### Phase 7: Add Save/Load (Preserve what you created!)

- [ ] 8. Implement project persistence
  - [ ] 8.1 Implement Application Controller
    - Create ApplicationController class
    - Implement project state management
    - Write tests for controller and state
    - _Requirements: 7, 8.2, 8.2.2, 9_
  
  - [ ] 8.2 Implement save functionality
    - Serialize to .rig.zip archive
    - Include parameters, geometry, PNG, CSV
    - Write tests for save
    - _Requirements: 8.2_
  
  - [ ] 8.3 Implement load functionality
    - Deserialize from .rig.zip
    - Restore UI state
    - **VISUAL MILESTONE**: Save and reload your designs! 🎉
    - Write tests for load and round-trip
    - _Requirements: 8.2_
  
  - [ ] 8.4 Add File menu actions
    - Implement New, Open, Save, Save As, Quit
    - Add unsaved changes warning
    - Write tests for menu actions
    - _Requirements: 8.2, 8.2.1, 8.2.2_

### Phase 8: Add Export and Polish

- [ ] 9. Add export and final features
  - [ ] 9.1 Implement DXF export
    - Export to DXF with separate layers
    - Add Export menu action
    - Write tests for DXF export
    - _Requirements: 8.2.1_
  
  - [ ] 9.2 Add rod enumeration display
    - Create enumeration markers (circles/squares)
    - Add toggle in View menu
    - **VISUAL MILESTONE**: See rod numbers! 🎉
    - Write test for enumeration
    - _Requirements: 7.3_
  
  - [ ] 9.3 Implement configuration management
    - Set up Hydra configuration loading
    - Implement QSettings for user preferences
    - Write tests for config loading
    - _Requirements: 10, 8.2.2_
  
  - [ ] 9.4 Add error handling and polish
    - Add error dialogs and logging
    - Verify performance optimizations
    - Write integration tests for complete workflows
    - _Requirements: All_

### Phase 9: Optional Advanced Features

- [ ]* 10. Advanced UI testing with pytest-qt
  - [ ]* 10.1 Write UI tests for parameter panel
  - [ ]* 10.2 Write UI tests for viewport
  - [ ]* 10.3 Write UI tests for BOM table
  - [ ]* 10.4 Write UI tests for progress dialog

## Visual Milestones Summary

1. ✅ Empty window with viewport (Task 2.2)
2. 🎯 First stair shape visible (Task 2.4)
3. 🎯 Switch between shapes (Task 3.3)
4. 🎯 First random infill (Task 4.3)
5. 🎯 Generation progress (Task 4.4)
6. 🎯 Quality improving (Task 5.4)
7. 🎯 Adjust parameters (Task 6.1)
8. 🎯 Parts list (Task 7.2)
9. 🎯 Highlight parts (Task 7.3)
10. 🎯 Save/load designs (Task 8.3)
11. 🎯 Rod numbers (Task 9.2)

## Notes

- **Every task includes at least one test**
- **Visual feedback at every major milestone**
- Each phase delivers a working, visible feature
- You can approve each feature before moving to the next
- Run after every change: `uv run mypy src/ && uv run ruff check . && uv run pytest --cov=railing_generator --cov-report=term-missing`
- Aim for >80% coverage on new code
