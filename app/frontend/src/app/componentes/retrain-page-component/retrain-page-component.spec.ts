import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RetrainPageComponent } from './retrain-page-component';

describe('RetrainPageComponent', () => {
  let component: RetrainPageComponent;
  let fixture: ComponentFixture<RetrainPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RetrainPageComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(RetrainPageComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
