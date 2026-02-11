import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LogsPanelComponent } from './logs-panel-component';

describe('LogsPanelComponent', () => {
  let component: LogsPanelComponent;
  let fixture: ComponentFixture<LogsPanelComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LogsPanelComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LogsPanelComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
