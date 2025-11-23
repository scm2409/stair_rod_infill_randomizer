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

- [x] 2. Create minimal UI skeleton to see shapes
  - [x] 2.1 Implement Rod class (Pydantic BaseModel) - needed for shapes
    - Define fields: geometry (LineString), start_cut_angle_deg, end_cut_angle_deg, weight_kg_m, layer
    - Implement computed fields: length_cm, weight_kg, start_point, end_point
    - Write unit tests for Rod class
    - _Requirements: 1, 5, 6, 8_
  
  - [x] 2.2 Create basic Main Window with viewport
    - Create MainWindow class (QMainWindow) with menu bar
    - Create ViewportWidget (QGraphicsView/QGraphicsScene)
    - Implement zoom and pan
    - Write test to verify window and viewport creation
    - **VISUAL MILESTONE**: Empty window with working viewport ✅
    - _Requirements: 7, 7.2_
  
  - [x] 2.3 Implement StaircaseRailingShape (first shape to visualize!)
    - Create StaircaseRailingShapeDefaults dataclass
    - Create StaircaseRailingShapeParameters Pydantic model
    - Create RailingFrame immutable container
    - Implement `generate_frame()` returning RailingFrame
    - Write unit tests for StaircaseRailingShape and RailingFrame
    - _Requirements: 2, 4, 5_
  
  - [x] 2.4 Connect shape to viewport rendering
    - Implement `set_railing_frame()` in viewport (render rods as lines)
    - Hard-code a StaircaseRailingShape instance for now
    - **VISUAL MILESTONE**: See your first stair shape! 🎉
    - Write test to verify frame rendering
    - _Requirements: 7, 7.1_

### Phase 2: (Reserved for future tasks)

_This phase is intentionally empty to keep phase numbers aligned with task numbers._

### Phase 3: Implement Central State Management (Foundation for all features!)

- [x] 3. Implement RailingProjectModel and ApplicationController
  - [x] 3.1 Create RailingProjectModel class
    - Create RailingProjectModel inheriting from QObject
    - Define all state fields (shape type, parameters, RailingFrame, generator type, parameters, RailingInfill, file path, modified flag, UI state)
    - Define all signals with proper naming (railing_shape_type_changed, railing_frame_updated, railing_infill_updated, etc.)
    - Implement property getters for all state fields
    - Write unit tests for model initialization
    - _Requirements: 7, 8.2, 8.2.2_
  
  - [x] 3.2 Implement state setter methods with signal emissions
    - Implement set_railing_shape_type() - clears frame, emits signals
    - Implement set_railing_shape_parameters() - marks modified, emits signal
    - Implement set_railing_frame() - clears infill, marks modified, emits signals
    - Implement set_generator_type() - marks modified, emits signal
    - Implement set_generator_parameters() - marks modified, emits signal
    - Implement set_railing_infill() - marks modified, emits signal
    - Implement set_project_file_path() - emits signal
    - Implement mark_project_saved() - clears modified flag, emits signal
    - Implement set_enumeration_visible() - emits signal
    - Write unit tests for each setter (verify signal emissions and state dependencies)
    - _Requirements: 7, 8.2, 8.2.2_
  
  - [x] 3.3 Implement utility methods
    - Implement reset_to_defaults() - clears all state, emits all signals
    - Implement has_railing_frame() - checks if frame exists
    - Implement has_railing_infill() - checks if infill exists
    - Write unit tests for utility methods
    - _Requirements: 8.2.2_
  
  - [x] 3.4 Create basic ApplicationController
    - Create ApplicationController class that takes RailingProjectModel in constructor
    - Implement update_railing_shape(shape_type, parameters) - creates RailingShape, generates frame, updates model
    - Implement create_new_project() - calls model.reset_to_defaults()
    - Create RailingShapeFactory to instantiate shapes from type string
    - Write unit tests for controller methods (verify model is updated correctly)
    - _Requirements: 4, 7, 8.2.2_
  
  - [x] 3.5 Refactor existing code to use RailingProjectModel and ApplicationController
    - Create RailingProjectModel and ApplicationController instances in main application
    - Connect ViewportWidget to model signals (railing_frame_updated, railing_infill_updated)
    - Update ViewportWidget to observe model instead of direct calls
    - Connect MainWindow to model signals (project_file_path_changed, project_modified_changed)
    - Update window title logic to observe model
    - Update "Update Shape" button to call controller.update_railing_shape()
    - Remove direct state management from UI components
    - **VISUAL MILESTONE**: Existing features now use central state management! 🎉
    - Write integration tests (controller updates model, model notifies UI)
    - _Requirements: 7, 8.2.2_

### Phase 4: Add Shape Selection (Choose and see different shapes!)

- [x] 4. Add shape selection UI
  - [x] 4.1 Implement RectangularRailingShape
    - Create RectangularRailingShapeDefaults dataclass
    - Create RectangularRailingShapeParameters Pydantic model  
    - Implement `generate_frame()` returning RailingFrame
    - Write unit tests for RectangularRailingShape
    - _Requirements: 3, 4, 5_
  
  - [x] 4.2 Create RailingShape factory and base class
    - RailingShape ABC already exists
    - Implement factory to create shapes from type string
    - Write tests for factory
    - _Requirements: 4_
  
  - [x] 4.3 Add parameter panel for shape selection
    - Create ParameterPanel widget with shape type dropdown
    - Add "Update Shape" button
    - Connect to viewport to render selected shape
    - **VISUAL MILESTONE**: Switch between stair and rectangular shapes! 🎉
    - Write test to verify panel and shape switching
    - _Requirements: 5, 6, 7_

### Phase 5: First Infill Generation (See rods being generated!)

- [x] 5. Implement random generators (V1 and V2)
  - [x] 5.1 Create RailingInfill class
    - Define immutable container with fields: rods (list), fitness_score (optional), iteration_count (optional), duration_sec (optional)
    - Make frozen (immutable)
    - Write unit tests
    - ✅ COMPLETED
    - _Requirements: 1, 6.2, 9_
  
  - [x] 5.2 Implement RandomGeneratorV1 and RandomGeneratorV2
    - Create Generator base class with signals
    - Implement RandomGeneratorV1 with simple random placement
    - Implement RandomGeneratorV2 with 4-phase algorithm (anchor, vertical, diagonal, gap-filling)
    - Respect basic constraints (no crossings in same layer, within boundary)
    - Accept RailingFrame as input, return RailingInfill
    - Write unit tests for both generators
    - ✅ COMPLETED
    - _Requirements: 1, 4.1, 6.1, 9_
  
  - [x] 5.3 Add generator UI and connect to viewport
    - Add generator type dropdown to parameter panel (random_v1, random_v2)
    - Add "Generate Infill" button
    - Implement `set_railing_infill()` in viewport (with layer colors)
    - **VISUAL MILESTONE**: See your first random infill! 🎉
    - Write test to verify infill rendering
    - ✅ COMPLETED
    - _Requirements: 6.1, 7, 9_
  
  - [x] 5.4 Add progress dialog for generation
    - Create ProgressDialog showing iteration count
    - Implement worker thread pattern for background generation
    - **VISUAL MILESTONE**: See generation progress in real-time! 🎉
    - Write test to verify progress dialog
    - ✅ COMPLETED
    - _Requirements: 9.1, 9.1.1_

**Note**: Random Generator V2 was implemented outside this task document. Both V1 and V2 are now available but currently run without evaluators.

### Phase 6: Add Evaluation System (See better results!)

- [ ] 6. Implement evaluator architecture (Pass-Through first, then Quality)
  - [x] 6.1 Create evaluator base classes and Pass-Through Evaluator
    - Create Evaluator ABC with `evaluate()` and `is_acceptable()` methods
    - Create EvaluatorParameters base class (Pydantic)
    - Create PassThroughEvaluatorParameters (empty Pydantic model)
    - Implement PassThroughEvaluator (always returns fitness=1.0, is_acceptable=True)
    - Create conf/evaluators/passthrough.yaml config
    - Write unit tests for Pass-Through Evaluator
    - ✅ COMPLETED
    - _Requirements: 6.2_
  
  - [x] 6.2 Connect Pass-Through Evaluator to RandomGeneratorV2 (required)
    - Update RandomGeneratorV2 to require evaluator parameter
    - Update RandomGeneratorV2Parameters to include evaluator_type field
    - Create EvaluatorFactory to instantiate evaluators from type string
    - Update conf/generators/random_v2.yaml to include evaluator_type: "passthrough"
    - Update ApplicationController to create evaluator and pass to generator
    - **VISUAL MILESTONE**: Generator V2 now uses evaluator architecture! 🎉
    - Write integration tests (generator V2 with pass-through evaluator)
    - _Requirements: 6.2, 9_
  
  - [ ] 6.3 Create Quality Evaluator structure with dummy implementations
    - Create QualityEvaluatorCriteriaDefaults dataclass
    - Create QualityEvaluatorParameters (Pydantic) with criteria weights
    - Implement QualityEvaluator class with `evaluate()` and `is_acceptable()` methods
    - Use dummy/placeholder implementations for quality criteria (return 0.5 for now)
    - Add TODO comments for hole identification and quality criteria implementations
    - Create conf/evaluators/quality.yaml config
    - Register QualityEvaluator in EvaluatorFactory
    - Write basic unit tests for evaluator structure
    - _Requirements: 6.2, 6.2.1_
  
  - [ ] 6.4 Implement hole identification
    - Implement function using `shapely.node()` and `polygonize()`
    - Replace dummy implementation in QualityEvaluator
    - Write unit tests for hole identification
    - _Requirements: 6.2, 6.2.1_
  
  - [ ] 6.5 Implement quality criteria
    - Implement hole uniformity criterion
    - Implement incircle uniformity criterion
    - Implement angle distribution criterion
    - Implement anchor spacing criterion
    - Replace dummy implementations in QualityEvaluator with actual criteria
    - Write unit tests for each criterion
    - _Requirements: 6.2.1_
  
  - [ ] 6.6 Enable Quality Evaluator in RandomGeneratorV2
    - Add evaluator_type dropdown to parameter panel
    - Add quality criteria parameter inputs (shown when quality evaluator selected)
    - Update progress dialog to show fitness score
    - Update conf/generators/random_v2.yaml to support evaluator_type: "quality"
    - **VISUAL MILESTONE**: See quality improving over iterations in V2! 🎉
    - Write integration tests (generator V2 with quality evaluator)
    - _Requirements: 1.1, 6.2, 6.3, 9.1.1_
  
  - [ ]* 6.7 Optionally add evaluator support to RandomGeneratorV1
    - Update RandomGeneratorV1 to optionally accept evaluator parameter
    - Update RandomGeneratorV1Parameters to include optional evaluator_type field
    - Update conf/generators/random_v1.yaml to support evaluator_type (optional)
    - Write integration tests (generator V1 with evaluators)
    - _Requirements: 6.2, 9_

**Note**: Evaluators are required for RandomGeneratorV2 but optional for RandomGeneratorV1.

### Phase 7: Add Parameter Controls (Fine-tune what you see!)

- [ ] 7. Add full parameter controls
  - [ ] 7.1 Implement dynamic parameter forms
    - Add shape parameter inputs (QDoubleSpinBox, QSpinBox)
    - Add generator parameter inputs
    - Show/hide based on selected type
    - Load defaults from Hydra config
    - **VISUAL MILESTONE**: Adjust parameters and see changes! 🎉
    - Write tests for parameter forms
    - _Requirements: 5, 6, 6.1, 10_
  
  - [ ] 7.2 Implement parameter validation
    - Connect Pydantic validation to UI
    - Display inline error messages
    - Write tests for validation display
    - _Requirements: 5, 9.2_

### Phase 8: Add BOM Table (See the parts list!)

- [ ] 8. Implement BOM table
  - [ ] 8.1 Create BOM Table widget
    - Create BOMTableWidget with two tabs (Frame/Infill)
    - Set up columns and sorting
    - Write test for table structure
    - _Requirements: 8_
  
  - [ ] 8.2 Populate BOM data
    - Populate from shape and infill result
    - Calculate and display totals
    - **VISUAL MILESTONE**: See parts list with totals! 🎉
    - Write tests for data population and totals
    - _Requirements: 8_
  
  - [ ] 8.3 Add BOM selection highlighting
    - Connect row selection to viewport highlighting
    - **VISUAL MILESTONE**: Click BOM row to highlight part! 🎉
    - Write test for selection
    - _Requirements: 8.1_

### Phase 9: Add Save/Load (Preserve what you created!)

- [ ] 9. Implement project persistence
  - [ ] 9.1 Extend ApplicationController for save/load
    - Implement save_project(file_path) - serializes model state to .rig.zip
    - Implement load_project(file_path) - deserializes and restores model state
    - Implement _serialize_project_state() - converts model to dict
    - Implement _deserialize_project_state() - restores model from dict
    - Write unit tests for serialization/deserialization
    - _Requirements: 8.2, 8.2.2_
  
  - [ ] 9.2 Implement save functionality
    - Serialize to .rig.zip archive
    - Include parameters, geometry, PNG, CSV
    - Write tests for save
    - _Requirements: 8.2_
  
  - [ ] 9.3 Implement load functionality
    - Deserialize from .rig.zip
    - Restore UI state
    - **VISUAL MILESTONE**: Save and reload your designs! 🎉
    - Write tests for load and round-trip
    - _Requirements: 8.2_
  
  - [ ] 9.4 Add File menu actions
    - Implement New, Open, Save, Save As, Quit
    - Add unsaved changes warning
    - Write tests for menu actions
    - _Requirements: 8.2, 8.2.1, 8.2.2_

### Phase 10: Add Export and Polish

- [ ] 10. Add export and final features
  - [ ] 10.1 Implement DXF export
    - Export to DXF with separate layers
    - Add Export menu action
    - Write tests for DXF export
    - _Requirements: 8.2.1_
  
  - [ ] 10.2 Add rod enumeration display
    - Create enumeration markers (circles/squares)
    - Add toggle in View menu
    - **VISUAL MILESTONE**: See rod numbers! 🎉
    - Write test for enumeration
    - _Requirements: 7.3_
  
  - [ ] 10.3 Implement configuration management
    - Set up Hydra configuration loading
    - Implement QSettings for user preferences
    - Write tests for config loading
    - _Requirements: 10, 8.2.2_
  
  - [ ] 10.4 Add error handling and polish
    - Add error dialogs and logging
    - Verify performance optimizations
    - Write integration tests for complete workflows
    - _Requirements: All_

### Phase 11: Optional Advanced Features

- [ ]* 11. Advanced UI testing with pytest-qt
  - [ ]* 11.1 Write UI tests for parameter panel
  - [ ]* 11.2 Write UI tests for viewport
  - [ ]* 11.3 Write UI tests for BOM table
  - [ ]* 11.4 Write UI tests for progress dialog

## Visual Milestones Summary

1. ✅ Empty window with viewport (Task 2.2)
2. ✅ First stair shape visible (Task 2.4)
3. ✅ Central state management integrated (Task 3.5)
4. ✅ Switch between shapes (Task 4.3)
5. ✅ First random infill with V1 and V2 (Task 5.3)
6. ✅ Generation progress (Task 5.4)
7. 🎯 Evaluator architecture integrated (Task 6.2)
8. 🎯 Quality improving over iterations (Task 6.5)
9. 🎯 Adjust parameters (Task 7.1)
10. 🎯 Parts list (Task 8.2)
11. 🎯 Highlight parts (Task 8.3)
12. 🎯 Save/load designs (Task 9.3)
13. 🎯 Rod numbers (Task 10.2)

## Notes

- **Every task includes at least one test**
- **Visual feedback at every major milestone**
- Each phase delivers a working, visible feature
- You can approve each feature before moving to the next
- Run after every change: `uv run mypy src/ && uv run ruff check . && uv run pytest --cov=railing_generator --cov-report=term-missing`
- Aim for >80% coverage on new code
