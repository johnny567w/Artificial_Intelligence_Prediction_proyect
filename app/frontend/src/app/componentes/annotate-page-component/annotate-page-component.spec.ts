import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AnnotatePageComponent } from './annotate-page-component';

describe('AnnotatePageComponent', () => {
  let component: AnnotatePageComponent;
  let fixture: ComponentFixture<AnnotatePageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AnnotatePageComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AnnotatePageComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
